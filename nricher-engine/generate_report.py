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

SÉCURITÉ — TOKEN API
----------------------
Le token est un secret par entreprise (donne accès aux vraies données client).
Il ne doit JAMAIS être écrit en clair dans un fichier versionné. Il se
configure via un fichier .env (gitignored) — copier .env.example vers .env et
renseigner NRICHER_API_TOKEN.

USAGE
-----
    python3 generate_report.py --company-id 11
    python3 generate_report.py --company-id 11 --weeks 26
    python3 generate_report.py --data data/_sample_api_response.json   # test sans token
"""

import argparse
import math
import os
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


COLOR_CHEAPER = "#10b981"
COLOR_EQUAL = "#3b82f6"
COLOR_PRICIER = "#ef4444"


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
    entreprise.
    """
    if not price_index_global_delta or price_index_global_delta.get("good") is None:
        return "neutral"
    return "good" if price_index_global_delta["good"] else "bad"


def fetch_weekly_kpis(company_id, weeks=13):
    """
    Récupère les données Weekly KPIs déjà calculées depuis l'API nricher.
    Nécessite NRICHER_API_TOKEN (et optionnellement NRICHER_API_BASE_URL) dans
    un fichier .env local — voir .env.example. Le token est propre à l'entreprise
    (page "APIs" de l'administration nricher) et ne doit jamais être commité.
    """
    base_url = os.environ.get("NRICHER_API_BASE_URL", "https://api.nricher.io")
    token = os.environ.get("NRICHER_API_TOKEN")
    if not token:
        raise RuntimeError(
            "NRICHER_API_TOKEN manquant. Copier nricher-engine/.env.example vers "
            "nricher-engine/.env et renseigner le token de l'entreprise."
        )

    response = requests.get(
        f"{base_url}/v1/weekly-kpis/{company_id}",
        params={"token": token, "weeks": weeks},
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

    for row in data["priorityTable"]:
        for key in ("top", "middle", "low"):
            row[f"{key}Severity"] = compute_pi_severity(row.get(key))
        row["allAvgMin1PSeverity"] = compute_pi_severity(row.get("allAvgMin1P"))
        row["allAvgMin3PSeverity"] = compute_pi_severity(row.get("allAvgMin3P"))

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

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

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
