#!/usr/bin/env python3
"""
generate_index.py
==================

Genere les pages de recherche d'entreprises :
  1. output/index.html        -> outil local (style autonome), pour usage interne
  2. ../recherche.html         -> page integree au site nricher.io (meme charte,
                                   nav/footer du site), exclue de l'index des
                                   moteurs de recherche (meta robots noindex)

AUTO-DECOUVERTE
---------------
La liste des entreprises (data/companies.json) est automatiquement
completee : chaque fichier data/<entreprise>.json (hors fichiers commencant
par "_") est lu, et si son meta.company_name n'est pas deja dans
companies.json, il y est ajoute et le fichier est resauvegarde.
Resultat : il suffit de deposer un nouveau data/<entreprise>.json pour que
l'entreprise apparaisse automatiquement dans la recherche, sans toucher au
code ni a companies.json a la main.

Une entreprise est marquee "disponible" si un rapport existe deja dans
output/<slug>.html (genere par generate_report.py).
"""

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
SITE_DIR = BASE_DIR.parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"
COMPANIES_FILE = DATA_DIR / "companies.json"


def slugify(name):
    return name.lower().replace(" ", "_")


def load_companies():
    if COMPANIES_FILE.exists():
        return json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))
    return []


def discover_new_companies(known_names):
    """Scanne data/*.json (hors _*.json) et renvoie les company_name absents de known_names."""
    known_slugs = {slugify(n) for n in known_names}
    discovered = []
    for jp in sorted(DATA_DIR.glob("*.json")):
        if jp.name.startswith("_") or jp == COMPANIES_FILE:
            continue
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
            name = data.get("meta", {}).get("company_name")
        except (json.JSONDecodeError, AttributeError):
            continue
        if name and slugify(name) not in known_slugs:
            discovered.append(name)
            known_slugs.add(slugify(name))
    return discovered


def main():
    companies = load_companies()

    new_companies = discover_new_companies(companies)
    if new_companies:
        companies.extend(new_companies)
        COMPANIES_FILE.write_text(
            json.dumps(companies, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"{len(new_companies)} nouvelle(s) entreprise(s) detectee(s) et ajoutee(s) a companies.json :")
        for n in new_companies:
            print(f"  + {n}")

    existing_slugs = {p.stem for p in OUTPUT_DIR.glob("*.html") if p.stem != "index"}

    rows = []
    for name in companies:
        slug = slugify(name)
        rows.append({"name": name, "slug": slug, "available": slug in existing_slugs})
    rows.sort(key=lambda r: r["name"].lower())

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    # 1. Outil local autonome
    OUTPUT_DIR.mkdir(exist_ok=True)
    engine_html = env.get_template("index_template.html").render(companies=rows)
    (OUTPUT_DIR / "index.html").write_text(engine_html, encoding="utf-8")

    # 2. Page integree au site (charte nricher.io, exclue des moteurs de recherche)
    site_html = env.get_template("site_search_template.html").render(companies=rows)
    (SITE_DIR / "recherche.html").write_text(site_html, encoding="utf-8")

    available_count = sum(1 for r in rows if r["available"])
    print(f"\n{available_count}/{len(rows)} rapports disponibles")
    print(f"Outil local : {OUTPUT_DIR / 'index.html'}")
    print(f"Page du site : {SITE_DIR / 'recherche.html'}")


if __name__ == "__main__":
    main()
