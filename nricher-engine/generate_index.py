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

Deux notions de disponibilite, volontairement distinctes :
  - output/index.html (outil local) : disponible = brouillon present dans
    output/<slug>.html (genere par generate_report.py, pas encore publie).
  - ../recherche.html (page du site) : disponible = rapport publie dans
    ../rapports/<slug>.html (copie la par sync_reports.py apres validation).
"""

import json
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
SITE_DIR = BASE_DIR.parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
RAPPORTS_DIR = SITE_DIR / "rapports"
DATA_DIR = BASE_DIR / "data"
COMPANIES_FILE = DATA_DIR / "companies.json"
INDEX_HTML = SITE_DIR / "index.html"


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

    draft_slugs = {p.stem for p in OUTPUT_DIR.glob("*.html") if p.stem != "index"}
    published_slugs = {p.stem for p in RAPPORTS_DIR.glob("*.html")} if RAPPORTS_DIR.exists() else set()

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

    # 1. Outil local autonome (reflete les brouillons dans output/)
    draft_rows = [
        {"name": n, "slug": slugify(n), "available": slugify(n) in draft_slugs}
        for n in companies
    ]
    draft_rows.sort(key=lambda r: r["name"].lower())
    OUTPUT_DIR.mkdir(exist_ok=True)
    engine_html = env.get_template("index_template.html").render(companies=draft_rows)
    (OUTPUT_DIR / "index.html").write_text(engine_html, encoding="utf-8")

    # 2. Page integree au site (reflete les rapports publies dans ../rapports/)
    site_rows = [
        {"name": n, "slug": slugify(n), "available": slugify(n) in published_slugs}
        for n in companies
    ]
    site_rows.sort(key=lambda r: r["name"].lower())
    site_html = env.get_template("site_search_template.html").render(companies=site_rows)
    (SITE_DIR / "recherche.html").write_text(site_html, encoding="utf-8")

    # 3. Injection des donnees dans la barre de recherche de la page d'accueil
    inject_companies_into_index(site_rows)

    print(f"\nOutil local   : {len(draft_slugs)}/{len(companies)} brouillons  -> {OUTPUT_DIR / 'index.html'}")
    print(f"Page du site  : {len(published_slugs)}/{len(companies)} publies    -> {SITE_DIR / 'recherche.html'}")


def inject_companies_into_index(site_rows):
    """Remplace le contenu de <script id="nricher-companies-data"> dans index.html
    par la liste a jour des entreprises (nom, slug, disponibilite), pour la barre
    de recherche autocomplete du hero."""
    if not INDEX_HTML.exists():
        return
    html = INDEX_HTML.read_text(encoding="utf-8")
    payload = json.dumps(
        [{"name": r["name"], "slug": r["slug"], "available": r["available"]} for r in site_rows],
        ensure_ascii=False,
    )
    new_tag = f'<script id="nricher-companies-data">window.NRICHER_COMPANIES = {payload};</script>'
    pattern = r'<script id="nricher-companies-data">.*?</script>'
    if re.search(pattern, html, flags=re.DOTALL):
        html = re.sub(pattern, new_tag, html, flags=re.DOTALL)
        INDEX_HTML.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
