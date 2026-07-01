#!/usr/bin/env python3
"""
generate_market_analysis.py
============================

Génère les fichiers JSON statiques pour les 3 piliers d'analyse de marché
(Pricing, Quality, Catalogue). Même principe que generate_all_reports.py :
le script tourne côté serveur (GitHub Actions) avec NRICHER_SITE_TOKEN et
écrit des fichiers statiques servis par GitHub Pages — zéro appel API
côté browser, zéro problème CORS.

Structure générée dans data/market-analysis/ à la racine du repo :
    categories.json
    pricing/<categoryId>.json
    pricing/<categoryId>/<slug>.json
    quality/<categoryId>.json
    quality/<categoryId>/<slug>.json
    catalogue/<categoryId>/<packIndex>.json   (0.json, 1.json, …)

USAGE
-----
    python3 generate_market_analysis.py
"""

import json
import sys
from pathlib import Path
from urllib.parse import quote

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os

BASE_URL = os.getenv("NRICHER_API_BASE_URL", "https://api.nricher.io")
SITE_TOKEN = os.getenv("NRICHER_SITE_TOKEN", "")

# Sortie : data/market-analysis/ à la racine du repo
OUT_DIR = Path(__file__).parent.parent / "data" / "market-analysis"


def auth_headers():
    return {"Authorization": f"Bearer {SITE_TOKEN}"}


def api_get(path):
    resp = requests.get(f"{BASE_URL}{path}", headers=auth_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    if not SITE_TOKEN:
        print("NRICHER_SITE_TOKEN manquant dans l'environnement.", file=sys.stderr)
        sys.exit(1)

    print(f"API  : {BASE_URL}")
    print(f"Vers : {OUT_DIR}\n")

    # ── Catégories ────────────────────────────────────────────────────────────
    try:
        categories = api_get("/v1/market-categories")
    except requests.RequestException as e:
        print(f"ERREUR /v1/market-categories : {e}", file=sys.stderr)
        sys.exit(1)

    write_json(OUT_DIR / "categories.json", categories)
    print(f"{len(categories)} catégorie(s) trouvée(s)\n")

    ok, failed = 0, 0

    for cat in categories:
        cat_id = cat["id"]
        companies = cat.get("companies", [])
        packs = cat.get("packs", [])
        print(f"[{cat_id}] {cat['name']} — {len(companies)} enseigne(s), {len(packs)} pack(s)")

        # ── Pricing overview ──────────────────────────────────────────────────
        pricing_slugs = []
        try:
            pricing_overview = api_get(f"/v1/market-analysis/pricing/{cat_id}")
            write_json(OUT_DIR / "pricing" / f"{cat_id}.json", pricing_overview)
            pricing_slugs = [r["slug"] for r in pricing_overview if r.get("slug")]
            print(f"  ✓ pricing overview ({len(pricing_slugs)} enseignes)")
            ok += 1
        except requests.RequestException as e:
            print(f"  ✗ pricing overview : {e}", file=sys.stderr)
            failed += 1

        # ── Pricing détail — slugs extraits de l'overview (source de vérité) ──
        for slug in pricing_slugs:
            try:
                write_json(
                    OUT_DIR / "pricing" / cat_id / f"{slug}.json",
                    api_get(f"/v1/market-analysis/pricing/{cat_id}/{slug}"),
                )
                ok += 1
            except requests.RequestException as e:
                print(f"  ✗ pricing/{slug} : {e}", file=sys.stderr)
                failed += 1

        # ── Quality overview ──────────────────────────────────────────────────
        quality_slugs = []
        try:
            quality_overview = api_get(f"/v1/market-analysis/quality/{cat_id}")
            write_json(OUT_DIR / "quality" / f"{cat_id}.json", quality_overview)
            quality_slugs = [r["slug"] for r in quality_overview if r.get("slug")]
            print(f"  ✓ quality overview ({len(quality_slugs)} enseignes)")
            ok += 1
        except requests.RequestException as e:
            print(f"  ✗ quality overview : {e}", file=sys.stderr)
            failed += 1

        # ── Quality détail — slugs extraits de l'overview ────────────────────
        for slug in quality_slugs:
            try:
                write_json(
                    OUT_DIR / "quality" / cat_id / f"{slug}.json",
                    api_get(f"/v1/market-analysis/quality/{cat_id}/{slug}"),
                )
                ok += 1
            except requests.RequestException as e:
                print(f"  ✗ quality/{slug} : {e}", file=sys.stderr)
                failed += 1

        # ── Catalogue par pack (nommés par index : 0.json, 1.json…) ──────────
        for i, pack_name in enumerate(packs):
            try:
                write_json(
                    OUT_DIR / "catalogue" / cat_id / f"{i}.json",
                    api_get(f"/v1/market-analysis/catalogue/{cat_id}/{quote(pack_name, safe='')}"),
                )
                print(f"  ✓ catalogue pack {i} ({pack_name})")
                ok += 1
            except requests.RequestException as e:
                print(f"  ✗ catalogue pack {i} ({pack_name}) : {e}", file=sys.stderr)
                failed += 1

    print(f"\n{ok} succès, {failed} échec(s) sur {len(categories)} catégorie(s)")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
