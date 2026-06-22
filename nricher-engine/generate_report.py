#!/usr/bin/env python3
"""
generate_report.py
===================

Moteur de génération des pages "Weekly KPIs" au format nricher.

CE QUE FAIT CE SCRIPT
----------------------
Prend un fichier JSON par entreprise (voir data/_schema_reference.json pour
le format exact), et génère une page HTML autonome dans output/, avec la
charte graphique réelle de nricher.io (couleurs, typos, composants) extraite
depuis leur propre CSS.

CE QUE CE SCRIPT NE FAIT PAS (volontairement)
----------------------------------------------
Il ne va chercher aucune donnée lui-même. Il ne se connecte à aucune base,
API ou compte nricher. Il prend en entrée un JSON déjà rempli, peu importe
sa provenance. C'est un choix de conception : brancher une vraie source de
données (API officielle nricher, export SFTP/Excel, scraping web public)
se fait en écrivant une fonction qui PRODUIT ce JSON, sans toucher au reste
du moteur.

IMPORTANT — DONNÉES CLIENTS
-----------------------------
Ce moteur ne doit être alimenté qu'avec :
  (a) des données de marché publiques (catalogues scrapés sur le web public,
      comme nricher le fait déjà pour son propre benchmark), ou
  (b) des données clients pour lesquelles l'autorisation explicite du client
      et de nricher a été obtenue.
Le champ meta.source_label est obligatoire et doit refléter honnêtement la
provenance de la donnée affichée sur la page elle-même.

USAGE
-----
    python3 generate_report.py --data data/exemple_fictif_demostore.json
    python3 generate_report.py --data data/*.json   # génère toutes les pages
"""

import json
import argparse
import glob
import math
import re
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_NAME = "report_template.html"

# Marge de l'échelle Y du graphique de tendance, en points d'indice prix
CHART_Y_PADDING = 3
SVG_X_LEFT = 40
SVG_X_RIGHT = 620
SVG_Y_TOP = 20
SVG_Y_BOTTOM = 200


def compute_multi_series_geometry(weeks, series):
    """
    Calcule les points SVG (polyline + cercles) pour plusieurs series partageant
    la meme echelle Y (ex: indice prix 1P/2P/3P sur un seul graphique), plus les
    libelles d'axe Y. `series` est un dict {nom: [valeurs...]}.
    Renvoie (dict nom -> {polyline, points}, y_max, y_mid, y_min).
    """
    all_values = [v for values in series.values() for v in values]
    if not all_values:
        return {name: {"polyline": "", "points": []} for name in series}, 100, 100, 100

    y_min = min(all_values) - CHART_Y_PADDING
    y_max = max(all_values) + CHART_Y_PADDING
    if y_max == y_min:
        y_max += 1  # évite une division par zéro si toutes les valeurs sont identiques

    n = len(weeks)
    step_x = (SVG_X_RIGHT - SVG_X_LEFT) / (n - 1) if n > 1 else 0

    result = {}
    for name, values in series.items():
        points = []
        for i, v in enumerate(values):
            x = SVG_X_LEFT + i * step_x
            # inversion d'axe : valeur haute -> y petit (en haut du SVG)
            y = SVG_Y_BOTTOM - ((v - y_min) / (y_max - y_min)) * (SVG_Y_BOTTOM - SVG_Y_TOP)
            points.append((round(x, 1), round(y, 1)))
        polyline_str = " ".join(f"{x},{y}" for x, y in points)
        result[name] = {"polyline": polyline_str, "points": points}

    y_mid = round((y_max + y_min) / 2)
    return result, round(y_max), y_mid, round(y_min)


GAUGE_CX, GAUGE_CY, GAUGE_R = 60, 58, 42
GAUGE_VMIN, GAUGE_VMAX = 90, 120


def compute_gauge_needle(value):
    """
    Calcule le point d'extremite de l'aiguille d'une jauge semi-circulaire
    (90 a gauche/vert, 120 a droite/rouge), a partir de la valeur du Price Index.
    """
    v = max(GAUGE_VMIN, min(GAUGE_VMAX, value))
    frac = (v - GAUGE_VMIN) / (GAUGE_VMAX - GAUGE_VMIN)
    angle_deg = 180 - frac * 180
    angle_rad = math.radians(angle_deg)
    x = GAUGE_CX + GAUGE_R * math.cos(angle_rad)
    y = GAUGE_CY - GAUGE_R * math.sin(angle_rad)
    return round(x, 1), round(y, 1)


def compute_gauge_bar_pct(value):
    """
    Remplissage (0-100%) de la barre sous chaque jauge, sur la meme echelle
    90-120 que l'aiguille (compute_gauge_needle) — les deux doivent toujours
    rester synchronises, d'ou la reutilisation des memes bornes GAUGE_VMIN/VMAX.
    """
    frac = (value - GAUGE_VMIN) / (GAUGE_VMAX - GAUGE_VMIN)
    return round(max(0, min(100, frac * 100)))


def compute_pi_severity(value):
    """
    Code couleur uniforme pour toute valeur de Price Index dans le rapport :
    vert sous 100, bleu pile a 100, rouge a partir de 101.
    """
    if value < 100:
        return "good"
    if value == 100:
        return "blue"
    return "bad"


def compute_gauge_delta_pct(value, ref_prev):
    """
    Calcule automatiquement la variation (ex: "-3%") entre la valeur actuelle d'une
    jauge et sa reference passee, en extrayant le nombre final de ref_prev (ex:
    "S24 : 104" -> 104). Remplace un champ qui etait jusque-la saisi a la main et
    pouvait se desynchroniser de la vraie valeur (ex: 104 -> 101 affiche "+1%").
    """
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*$", str(ref_prev))
    if not match:
        return None
    ref_value = float(match.group(1).replace(",", "."))
    if ref_value == 0:
        return None
    pct = (value - ref_value) / ref_value * 100
    return f"{pct:+.0f}%"


DONUT_CX, DONUT_CY, DONUT_R = 60, 60, 50


def compute_donut_segments(parts):
    """
    parts: liste de (pct, couleur_css). Renvoie les segments (dasharray/dashoffset)
    d'un donut SVG (cercle r=50, demarre a midi via rotate(-90) sur le <g> parent),
    plus la position (label_x, label_y) du milieu de chaque arc pour y afficher le %.
    """
    circumference = 2 * math.pi * DONUT_R
    segments = []
    cumulative = 0.0
    for pct, color in parts:
        length = circumference * (pct / 100.0)

        mid_fraction = (cumulative + length / 2) / circumference if circumference else 0
        angle = mid_fraction * 2 * math.pi
        x_unrot = DONUT_CX + DONUT_R * math.cos(angle)
        y_unrot = DONUT_CY + DONUT_R * math.sin(angle)
        # applique la meme rotation -90deg que le <g transform> du donut
        label_x = DONUT_CX + (y_unrot - DONUT_CY)
        label_y = DONUT_CY - (x_unrot - DONUT_CX)

        segments.append({
            "color": color,
            "pct": pct,
            "dasharray": f"{length:.2f} {circumference - length:.2f}",
            "dashoffset": f"{-cumulative:.2f}",
            "label_x": round(label_x, 1),
            "label_y": round(label_y, 1),
        })
        cumulative += length
    return segments


def compute_competitors_overview(competitors):
    """Moyenne simple Lower/Equal/Higher tous concurrents confondus + classement par PI."""
    n = len(competitors) or 1
    avg_lower = round(sum(c["lower_pct"] for c in competitors) / n)
    avg_equal = round(sum(c["equal_pct"] for c in competitors) / n)
    avg_higher = max(0, 100 - avg_lower - avg_equal)

    donut_segments = compute_donut_segments([
        (avg_lower, "var(--good)"),
        (avg_equal, "var(--blue)"),
        (avg_higher, "var(--bad)"),
    ])

    ranking = sorted(competitors, key=lambda c: c["pi"])
    for c in ranking:
        c["bar_pct"] = compute_gauge_bar_pct(c["pi"])

    return {
        "avg_lower": avg_lower, "avg_equal": avg_equal, "avg_higher": avg_higher,
        "donut_segments": donut_segments,
    }, ranking


def load_company_data(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_top_keys = [
        "meta", "hero", "price_index_gauges", "priority_table",
        "trend_chart", "attractiveness_stacked", "competitors",
        "competitors_table", "sellers_table", "sellers_stacked",
        "category_stacked", "verdict",
    ]
    missing = [k for k in required_top_keys if k not in data]
    if missing:
        raise ValueError(f"{json_path.name} : clés manquantes dans le JSON : {missing}")

    if "source_label" not in data.get("meta", {}) or not data["meta"]["source_label"]:
        raise ValueError(
            f"{json_path.name} : meta.source_label est obligatoire — "
            f"précise la provenance de la donnée (ex: 'Donnée publique scrapée')."
        )

    return data


def render_report(json_path, env):
    data = load_company_data(json_path)

    weeks = data["trend_chart"]["weeks"]
    series = {
        "1p": data["trend_chart"]["price_index_1p"],
        "2p": data["trend_chart"]["price_index_2p"],
        "3p": data["trend_chart"]["price_index_3p"],
    }
    series_geo, y_max, y_mid, y_min = compute_multi_series_geometry(weeks, series)

    for gauge in data["price_index_gauges"]["gauges"]:
        gauge["needle_x"], gauge["needle_y"] = compute_gauge_needle(gauge["value"])
        gauge["bar_pct"] = compute_gauge_bar_pct(gauge["value"])
        gauge["severity"] = compute_pi_severity(gauge["value"])
        computed_delta = compute_gauge_delta_pct(gauge["value"], gauge.get("ref_prev"))
        if computed_delta is not None:
            gauge["delta_pct"] = computed_delta

    competitors_overview, competitors_ranking = compute_competitors_overview(data["competitors"])

    template = env.get_template(TEMPLATE_NAME)
    html = template.render(
        meta=data["meta"],
        hero=data["hero"],
        price_index_gauges=data["price_index_gauges"],
        priority_table=data["priority_table"],
        trend_chart=data["trend_chart"],
        attractiveness_stacked=data["attractiveness_stacked"],
        competitors=data["competitors"],
        competitors_table=data["competitors_table"],
        competitors_overview=competitors_overview,
        competitors_ranking=competitors_ranking,
        sellers_table=data["sellers_table"],
        sellers_stacked=data["sellers_stacked"],
        category_stacked=data["category_stacked"],
        verdict=data["verdict"],
        series_geo=series_geo,
        chart_y_max=y_max,
        chart_y_mid=y_mid,
        chart_y_min=y_min,
    )

    company_slug = data["meta"]["company_name"].lower().replace(" ", "_")
    out_path = OUTPUT_DIR / f"{company_slug}.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Génère les pages Weekly KPIs nricher à partir de fichiers JSON.")
    parser.add_argument(
        "--data", nargs="+", required=True,
        help="Chemin(s) ou pattern(s) glob vers les fichiers JSON d'entreprise (ex: data/*.json)",
    )
    args = parser.parse_args()

    json_paths = []
    for pattern in args.data:
        matched = glob.glob(pattern)
        if not matched:
            print(f"⚠️  Aucun fichier ne correspond à : {pattern}", file=sys.stderr)
        json_paths.extend(matched)

    json_paths = [Path(p) for p in json_paths if not Path(p).name.startswith("_")]

    if not json_paths:
        print("Aucun fichier JSON valide à traiter. Abandon.", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    print(f"Génération de {len(json_paths)} page(s)...\n")
    for jp in sorted(json_paths):
        try:
            out_path = render_report(jp, env)
            print(f"  ✓ {jp.name:40s} → {out_path}")
        except Exception as e:
            print(f"  ✗ {jp.name:40s} → ERREUR : {e}", file=sys.stderr)

    print(f"\nTerminé. Pages disponibles dans {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
