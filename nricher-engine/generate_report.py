#!/usr/bin/env python3
"""
generate_report.py
===================

Moteur de génération des pages "Weekly KPIs" au format nricher.

CE QUE FAIT CE SCRIPT
----------------------
Récupère les données déjà calculées d'une entreprise depuis l'API nricher
(GET /v1/weekly-kpis/:companyId, voir fetch_weekly_kpis ci-dessous), et génère
une page HTML autonome dans output/, en reproduisant fidèlement le rendu réel
de l'app nricher (thème sombre, jauges, donut, graphiques, tables) — voir
handoff-dev/WEEKLY_KPIS_APP_SOURCE_OF_TRUTH.md pour la référence visuelle
complète et le contrat exact de l'API.

L'API renvoie des données déjà entièrement calculées (deltas, distributions
en %, verdict généré) — ce script n'a aucune logique métier à réimplémenter.
Il calcule uniquement la géométrie SVG pure (position d'aiguille de jauge,
segments du donut) à partir des valeurs brutes, à chaque affichage.

SÉCURITÉ — TOKENS
----------------------
Un seul secret persiste : NRICHER_SITE_TOKEN (JWT au niveau site, voir .env.example),
jamais écrit en clair dans un fichier versionné. Le token par entreprise
(donne accès aux vraies données client) n'est, lui, JAMAIS stocké : il est
re-créé à la volée à chaque génération via POST /v1/:companyId/create-api-token
(voir create_company_token), utilisé immédiatement, puis jeté. Cette création
écrase tout token existant pour cette entreprise — le stocker reviendrait à
le rendre fragile (invalidé dès qu'un autre appel le recrée ailleurs), d'où
le choix de toujours en minter un frais plutôt que d'en garder un en cache.

USAGE
-----
    python3 generate_report.py --company-id 11
    python3 generate_report.py --company-id 11 --weeks 26
    python3 generate_report.py --data data/_sample_api_response.json   # test sans token
"""

import argparse
import math
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_NAME = "report_template.html"

load_dotenv(BASE_DIR / ".env")

GAUGE_CX, GAUGE_CY, GAUGE_R = 100, 100, 80
GAUGE_VMIN, GAUGE_VMAX = 80, 120

PRIORITY_TABLE_WEEKS = 4  # 3 semaines d'historique + la semaine courante, comme l'app

# Entreprises clientes sous contrat dont les donnees ne doivent pas etre
# librement consultables tant qu'aucun mecanisme d'acces (login, lien a
# token) n'est en place cote site - voir handoff-dev pour le contexte.
# Comparaison insensible a la casse sur le nom de l'entreprise.
GATED_COMPANIES = {"conforama"}


def compute_gauge_needle(value):
    """
    Calcule le point d'extremite de l'aiguille d'une jauge semi-circulaire
    (80 a gauche, 120 a droite), a partir de la valeur du Price Index.
    """
    v = max(GAUGE_VMIN, min(GAUGE_VMAX, value))
    frac = (v - GAUGE_VMIN) / (GAUGE_VMAX - GAUGE_VMIN)
    angle_deg = 180 - frac * 180
    angle_rad = math.radians(angle_deg)
    x = GAUGE_CX + GAUGE_R * 0.76 * math.cos(angle_rad)
    y = GAUGE_CY - GAUGE_R * 0.76 * math.sin(angle_rad)
    return round(x, 1), round(y, 1)


def compute_gauge_bar_pct(value):
    """
    Position (0-100%) sur la barre de progression sous chaque jauge, sur la
    meme echelle 80-120 que l'aiguille (compute_gauge_needle) — les deux
    doivent toujours rester synchronises, d'ou les memes bornes GAUGE_VMIN/VMAX.
    """
    frac = (value - GAUGE_VMIN) / (GAUGE_VMAX - GAUGE_VMIN)
    return round(max(0, min(100, frac * 100)))


def compute_pi_severity(value):
    """
    Code couleur uniforme pour toute valeur de Price Index dans le rapport :
    vert sous 100, bleu pile a 100, rouge a partir de 101. Noms de classe CSS
    herites du gabarit existant (good/blue/bad) — seules les couleurs hex
    derriere --good/--blue/--bad changent pour matcher l'app (voir plus bas).
    """
    if value is None:
        return None
    if value < 100:
        return "good"
    if value == 100:
        return "blue"
    return "bad"


DONUT_CX, DONUT_CY, DONUT_R = 60, 60, 50
DONUT_GAP_DEG = 1.5


def compute_donut_segments(parts):
    """
    parts: liste de (pct, couleur_css). Renvoie les segments (dasharray/dashoffset)
    d'un donut en anneau (cercle stroke r=50, demarre a midi via rotate(-90) sur
    le <g> parent), avec un petit espace entre segments (DONUT_GAP_DEG), plus la
    position (label_x, label_y) du milieu de chaque arc pour y afficher le %.
    """
    circumference = 2 * math.pi * DONUT_R
    gap_length = circumference * (DONUT_GAP_DEG / 360)
    segments = []
    cumulative = 0.0
    for pct, color in parts:
        full_length = circumference * (pct / 100.0)
        drawn_length = max(0.0, full_length - gap_length)

        mid_fraction = (cumulative + full_length / 2) / circumference if circumference else 0
        angle = mid_fraction * 2 * math.pi
        x_unrot = DONUT_CX + DONUT_R * math.cos(angle)
        y_unrot = DONUT_CY + DONUT_R * math.sin(angle)
        # applique la meme rotation -90deg que le <g transform> du donut
        label_x = DONUT_CX + (y_unrot - DONUT_CY)
        label_y = DONUT_CY - (x_unrot - DONUT_CX)

        segments.append({
            "color": color,
            "pct": pct,
            "dasharray": f"{drawn_length:.2f} {circumference - drawn_length:.2f}",
            "dashoffset": f"{-cumulative:.2f}",
            "label_x": round(label_x, 1),
            "label_y": round(label_y, 1),
        })
        cumulative += full_length
    return segments


def append_live_point(data, competitors_overview):
    """
    Reproduit appendLivePoint() de l'app (commit 56c90581, nricher-workspace) :
    les graphiques de tendance ne tracent que les semaines deja completees,
    donc leur dernier point peut etre en retard sur les valeurs live affichees
    dans les jauges/le donut juste au-dessus (constate sur Simplybearings :
    jauge 1P min a 121, dernier point du graphique a 104). Ajoute un point
    final "Ajd" construit a partir de ces memes valeurs live, sur les deux
    graphiques, pour qu'ils restent coherents avec le reste de la page.
    """
    gauges_by_key = {g["key"]: g for g in data["gauges"]}

    data["trendChart"]["weeks"].append("Ajd")
    data["trendChart"]["priceIndex1P"].append(gauges_by_key.get("1P_MIN", {}).get("value"))
    data["trendChart"]["priceIndex3P"].append(gauges_by_key.get("3P_MIN", {}).get("value"))

    data["attractivenessStacked"].append({
        "week": "Ajd",
        "lowerPct": competitors_overview["avgLower"],
        "equalPct": competitors_overview["avgEqual"],
        "higherPct": competitors_overview["avgHigher"],
    })


COLOR_CHEAPER = "var(--good)"
COLOR_EQUAL = "var(--blue)"
COLOR_PRICIER = "var(--bad)"


def compute_competitors_overview(stacked):
    """
    Moyenne lower/equal/higher tous concurrents confondus (donut) + classement
    par PI. Plafonds repris de l'app : classement = 10 premiers (croissant par
    PI), liste "face aux concurrents" = 12 premiers (decroissant par volume).
    """
    n = len(stacked) or 1
    avg_lower = round(sum(c["lowerPct"] for c in stacked) / n)
    avg_equal = round(sum(c["equalPct"] for c in stacked) / n)
    avg_higher = max(0, 100 - avg_lower - avg_equal)

    donut_segments = compute_donut_segments([
        (avg_lower, COLOR_CHEAPER),
        (avg_equal, COLOR_EQUAL),
        (avg_higher, COLOR_PRICIER),
    ])

    ranking = sorted(stacked, key=lambda c: c["pi"])[:10]
    for c in ranking:
        c["barPct"] = compute_gauge_bar_pct(c["pi"])

    by_volume = sorted(stacked, key=lambda c: c["matched"], reverse=True)[:12]

    return {
        "avgLower": avg_lower, "avgEqual": avg_equal, "avgHigher": avg_higher,
        "donutSegments": donut_segments,
    }, ranking, by_volume


FRENCH_MONTHS_ABBR = [
    "jan.", "fév.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
]


def format_french_datetime(iso_string):
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return f"{dt.day:02d} {FRENCH_MONTHS_ABBR[dt.month - 1]} à {dt.hour:02d}h{dt.minute:02d}"


def compute_hero_tagline(price_index_global_delta):
    """
    L'API ne fournit pas de titre de hero (champ texte) — seulement les
    valeurs et leur delta deja calcule. Le gabarit du H1 ("Le marche a
    bouge. {tagline}") est donc genere ici a partir du sens du delta,
    avec un libelle statique traduisible (data-i18n), pas une donnee
    entreprise. "neutral" (bleu, comme le 100=aligne) couvre aussi bien
    l'absence de delta que le cas stable (delta a 0), comme corrige cote
    app (commit 42bb1e83 : couleur bleue, pas rouge, quand le prix tient bon).
    """
    if not price_index_global_delta:
        return "neutral"
    text = (price_index_global_delta.get("text") or "").strip()
    if re.match(r"^[+-]?0\b", text):
        return "neutral"
    if price_index_global_delta.get("good") is None:
        return "neutral"
    return "good" if price_index_global_delta["good"] else "bad"


def get_site_jwt_and_base_url():
    base_url = os.environ.get("NRICHER_API_BASE_URL", "https://api.nricher.io")
    jwt_token = os.environ.get("NRICHER_SITE_TOKEN")
    if not jwt_token:
        raise RuntimeError(
            "NRICHER_SITE_TOKEN manquant. Copier nricher-engine/.env.example vers "
            "nricher-engine/.env et renseigner le JWT site."
        )
    return base_url, jwt_token


def create_company_token(company_id, base_url, jwt_token):
    """
    Mint un token a la volee pour une entreprise (POST /v1/:companyId/create-api-token,
    authentifie par le JWT site). Cree-OU-ecrase : n'appeler que pour un usage
    immediat, jamais pour stocker le resultat (voir note securite en tete de fichier).
    """
    response = requests.post(
        f"{base_url}/v1/{company_id}/create-api-token",
        headers={"Authorization": f"Bearer {jwt_token}"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["companyApiToken"]


def fetch_weekly_kpis(company_id, weeks=13):
    """
    Recupere les donnees Weekly KPIs deja calculees depuis l'API nricher.
    Mint un token par-entreprise frais a la volee (jamais stocke, voir
    create_company_token), l'utilise immediatement pour cet appel, puis le
    jette. Necessite NRICHER_SITE_TOKEN dans .env (voir .env.example).
    """
    base_url, jwt_token = get_site_jwt_and_base_url()
    company_token = create_company_token(company_id, base_url, jwt_token)

    response = requests.get(
        f"{base_url}/v1/weekly-kpis/{company_id}",
        params={"token": company_token, "weeks": weeks},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def render_report(data, env):
    for gauge in data["gauges"]:
        if gauge["value"] is None:
            gauge["needleX"], gauge["needleY"] = compute_gauge_needle(
                (GAUGE_VMIN + GAUGE_VMAX) / 2
            )
            gauge["barPct"] = None
            gauge["refPct"] = None
            gauge["severity"] = None
        else:
            gauge["needleX"], gauge["needleY"] = compute_gauge_needle(gauge["value"])
            gauge["barPct"] = compute_gauge_bar_pct(gauge["value"])
            gauge["refPct"] = (
                compute_gauge_bar_pct(gauge["previousValue"])
                if gauge.get("previousValue") is not None else None
            )
            gauge["severity"] = compute_pi_severity(gauge["value"])

    data["visibleGauges"] = [g for g in data["gauges"] if g["key"] != "3P_SAME_MIN"]

    data["hero"]["priceIndexGlobalSeverity"] = compute_pi_severity(data["hero"]["priceIndexGlobal"])
    data["heroTagline"] = compute_hero_tagline(data["hero"].get("priceIndexGlobalDelta"))
    data["generatedAtLabel"] = format_french_datetime(data["generatedAt"])
    data["isGated"] = data["company"]["name"].strip().lower() in GATED_COMPANIES

    data["priorityTable"] = data["priorityTable"][-PRIORITY_TABLE_WEEKS:]
    for row in data["priorityTable"]:
        for key in ("top", "middle", "low"):
            row[f"{key}Severity"] = compute_pi_severity(row.get(key))
        row["allAvgMin1PSeverity"] = compute_pi_severity(row.get("allAvgMin1P"))
        row["allAvgMin3PSeverity"] = compute_pi_severity(row.get("allAvgMin3P"))

    # Plafonds repris tels quels du code reel de l'app (WeeklyKpisLayout.tsx) :
    # tables competitors/sellers et DistributionRow sellers -> 12, categories -> 14.
    data["competitors"]["table"] = data["competitors"]["table"][:12]
    data["sellers"]["table"] = data["sellers"]["table"][:12]
    data["sellers"]["stacked"] = data["sellers"]["stacked"][:12]
    data["categoryStacked"] = data["categoryStacked"][:14]

    for row in data["competitors"]["table"]:
        row["piAllSeverity"] = compute_pi_severity(row.get("piAll"))
        row["piMinSeverity"] = compute_pi_severity(row.get("piMin"))

    for row in data["sellers"]["table"]:
        row["piMinSeverity"] = compute_pi_severity(row.get("piMin"))

    for row in data["competitors"]["stacked"]:
        row["severity"] = compute_pi_severity(row.get("pi"))
    for row in data["sellers"]["stacked"]:
        row["severity"] = compute_pi_severity(row.get("pi"))
    for row in data["categoryStacked"]:
        row["severity"] = compute_pi_severity(row.get("pi"))

    competitors_overview, competitors_ranking, competitors_by_volume = compute_competitors_overview(
        data["competitors"]["stacked"]
    )
    append_live_point(data, competitors_overview)

    template = env.get_template(TEMPLATE_NAME)
    html = template.render(
        data=data,
        competitors_overview=competitors_overview,
        competitors_ranking=competitors_ranking,
        competitors_by_volume=competitors_by_volume,
        gauge_vmin=GAUGE_VMIN,
        gauge_vmax=GAUGE_VMAX,
    )

    company_slug = data["company"]["name"].lower().replace(" ", "_")
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{company_slug}.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def format_space_int(value):
    """
    Reproduit spaceLargeNumber() de l'app (espace comme separateur de
    milliers, ex: 155943 -> "155 943"), utilisable sur un int ou une
    chaine numerique. Renvoie la valeur telle quelle si elle n'est pas
    un nombre (ex: "-2 pts"), pour rester utilisable partout sans risque.
    """
    if value is None:
        return "—"
    try:
        n = int(value)
    except (TypeError, ValueError):
        return value
    return f"{n:,}".replace(",", " ")


def build_environment():
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    env.filters["space_int"] = format_space_int
    return env


def main():
    parser = argparse.ArgumentParser(
        description="Génère une page Weekly KPIs nricher à partir de l'API ou d'un JSON local."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--company-id", type=int, help="Identifiant nricher de l'entreprise (fetch API live)."
    )
    source.add_argument(
        "--data", help="Chemin vers un JSON local au format API (pour tester sans token)."
    )
    parser.add_argument(
        "--weeks", type=int, default=13,
        help="Semaines d'historique a recuperer (API uniquement, defaut 13).",
    )
    args = parser.parse_args()

    env = build_environment()

    try:
        if args.company_id is not None:
            print(f"Récupération des données entreprise #{args.company_id}...")
            data = fetch_weekly_kpis(args.company_id, weeks=args.weeks)
        else:
            import json
            data = json.loads(Path(args.data).read_text(encoding="utf-8"))

        out_path = render_report(data, env)
        print(f"✓ {data['company']['name']} → {out_path}")
    except Exception as e:
        print(f"✗ ERREUR : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
