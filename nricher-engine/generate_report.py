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
    python3 generate_report.py --data data/exemple_fictif.json
    python3 generate_report.py --data data/*.json   # génère toutes les pages
"""

import json
import argparse
import glob
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


def compute_chart_geometry(weeks, values):
    """
    Calcule les points SVG (polyline + cercles) et les libellés d'axe Y
    à partir d'une simple liste de valeurs d'indice prix.
    Évite de devoir pré-calculer des coordonnées pixel à la main dans le JSON.
    """
    if not values:
        return "", [], 100, 100, 100

    y_min = min(values) - CHART_Y_PADDING
    y_max = max(values) + CHART_Y_PADDING
    if y_max == y_min:
        y_max += 1  # évite une division par zéro si toutes les valeurs sont identiques

    n = len(values)
    step_x = (SVG_X_RIGHT - SVG_X_LEFT) / (n - 1) if n > 1 else 0

    points = []
    for i, v in enumerate(values):
        x = SVG_X_LEFT + i * step_x
        # inversion d'axe : valeur haute -> y petit (en haut du SVG)
        y = SVG_Y_BOTTOM - ((v - y_min) / (y_max - y_min)) * (SVG_Y_BOTTOM - SVG_Y_TOP)
        points.append((round(x, 1), round(y, 1)))

    polyline_str = " ".join(f"{x},{y}" for x, y in points)
    y_mid = round((y_max + y_min) / 2)

    return polyline_str, points, round(y_max), y_mid, round(y_min)


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
    values = data["trend_chart"]["price_index_3p"]
    polyline_str, points, y_max, y_mid, y_min = compute_chart_geometry(weeks, values)

    # le dernier point du tracé est mis en évidence (cercle plus gros + contour blanc)
    chart_circles = points

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
        sellers_table=data["sellers_table"],
        sellers_stacked=data["sellers_stacked"],
        category_stacked=data["category_stacked"],
        verdict=data["verdict"],
        chart_points=polyline_str,
        chart_circles=chart_circles,
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
