#!/usr/bin/env python3
"""
generate_market_analysis.py  (v3)
====================================

Génère les JSON statiques pour les 3 pages d'analyse de marché (Pricing,
Quality, Catalogue) en appelant les endpoints pré-calculés Monthly Analysis.

Zéro calcul côté script, zéro token par-entreprise — requêtes HTTP simples
sur des endpoints publics (aucun @UseGuards côté backend).

Endpoints utilisés :
  GET /monthly-analysis-pricing                 categoryId
  GET /monthly-analysis-pricing/evolution       categoryId
  GET /monthly-analysis-pricing/detail          categoryId, competitor
  GET /monthly-analysis-quality                 categoryId
  GET /monthly-analysis-quality/detail          categoryId, brand
  GET /monthly-analysis-catalogue               categoryId, pack

USAGE
-----
    python3 generate_market_analysis.py
"""

import json
import re
import sys
import time
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os

BASE_URL = os.getenv("NRICHER_API_BASE_URL", "https://api.nricher.io")
OUT_DIR = Path(__file__).parent.parent / "data" / "market-analysis"

REQUEST_DELAY = 0.2  # secondes entre appels

# Les 7 catégories de marché (MONTHLY_ANALYSIS_ANCHORS backend) avec leurs packs.
CATEGORIES = [
    {
        "id": "maison-deco",
        "name": "Maison & Décoration",
        "packs": ["Suspension", "Lampe à poser", "Applique murale", "Lampadaire", "Plafonnier"],
    },
    {
        "id": "bricolage-jardin",
        "name": "Bricolage & Jardin",
        "packs": ["Salon de jardin", "Canapé", "Matelas", "Lit", "Commode"],
    },
    {
        "id": "sport-outdoor",
        "name": "Sport & Outdoor",
        "packs": ["Chaussures de trail", "Chaussures de randonnée", "Sac à dos", "Veste", "T-shirt"],
    },
    {
        "id": "beaute-parfumerie",
        "name": "Beauté & Parfumerie",
        "packs": ["Maquillage", "Parfum", "Soin du visage", "Coffret"],
    },
    {
        "id": "electronique-hightech",
        "name": "Électronique & High-Tech",
        "packs": ["Smartphone", "Ordinateur portable", "Télévision", "Casque audio", "Tablette"],
    },
    {
        "id": "grande-distribution",
        "name": "Grande Distribution",
        "packs": ["Canapé", "Lit", "Matelas", "Fauteuil", "Table à manger"],
    },
    {
        "id": "marketplaces",
        "name": "Marketplaces en ligne",
        "packs": ["Smartphone", "Canapé", "Matelas", "Lit", "Table à manger"],
    },
]


def get(path, params=None):
    resp = requests.get(f"{BASE_URL}{path}", params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def as_list(body):
    return body if isinstance(body, list) else body.get("data", [])


def slugify(text):
    s = (text or "").lower()
    for src, dst in [
        ("à","a"),("â","a"),("ä","a"),("é","e"),("è","e"),("ê","e"),("ë","e"),
        ("î","i"),("ï","i"),("ô","o"),("ö","o"),("ù","u"),("û","u"),("ü","u"),
        ("ç","c"),("œ","oe"),("æ","ae"),("&","et"),
    ]:
        s = s.replace(src, dst)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    print(f"API  : {BASE_URL}")
    print(f"Vers : {OUT_DIR}\n")

    ok = failed = 0
    companies_by_cat = {}  # cat_id → [{slug, name}]

    for cat in CATEGORIES:
        cat_id  = cat["id"]
        cat_name = cat["name"]
        packs   = cat["packs"]
        print(f"── {cat_name} ({cat_id}) ──")

        # ── Pricing overview ──────────────────────────────────────────────
        pricing_rows = []
        try:
            raw = get("/monthly-analysis-pricing", {"categoryId": cat_id})
            for r in as_list(raw):
                pricing_rows.append({
                    "slug":             slugify(r.get("competitorKey") or r.get("brand", "")),
                    "competitorKey":    r.get("competitorKey") or r.get("brand", ""),
                    "name":             r.get("brand", ""),
                    "articlesAnalysed": r.get("analysed", 0),
                    "articlesMatched":  r.get("matched", 0),
                    "priceIndex":       r.get("pi"),
                })
            overview_out = [{k: v for k, v in r.items() if k != "competitorKey"} for r in pricing_rows]
            write_json(OUT_DIR / "pricing" / f"{cat_id}.json", overview_out)
            print(f"  ✓ pricing/{cat_id}.json ({len(pricing_rows)} enseignes)")
            ok += 1
        except Exception as e:
            print(f"  ✗ pricing overview : {e}", file=sys.stderr)
            failed += 1

        companies_by_cat[cat_id] = [{"slug": r["slug"], "name": r["name"]} for r in pricing_rows]

        # ── Pricing evolution (1 appel pour toute la catégorie) ───────────
        weeks = []
        comp_trends = []
        try:
            evo = as_list(get("/monthly-analysis-pricing/evolution", {"categoryId": cat_id}))
            if evo and evo[0].get("history"):
                weeks = [h.get("weekDate", "") for h in evo[0]["history"]]
            comp_trends = [
                {
                    "name":      c.get("competitor", ""),
                    "piHistory": [h.get("pi") for h in c.get("history", [])],
                }
                for c in evo
            ]
            print(f"  ✓ pricing/{cat_id}/evolution ({len(weeks)} semaines, {len(comp_trends)} concurrents)")
            ok += 1
        except Exception as e:
            print(f"  ✗ pricing evolution : {e}", file=sys.stderr)
            failed += 1

        # ── Pricing detail par enseigne ───────────────────────────────────
        for row in pricing_rows:
            slug = row["slug"]
            try:
                detail = get("/monthly-analysis-pricing/detail", {
                    "categoryId": cat_id,
                    "competitor": row["competitorKey"],
                })
                hist = detail.get("history", [])
                write_json(OUT_DIR / "pricing" / cat_id / f"{slug}.json", {
                    "slug":             slug,
                    "name":             row["name"],
                    "priceIndex":       row["priceIndex"],
                    "weeks":            weeks,
                    "competitorTrends": comp_trends,
                    "attractiveness": [
                        {
                            "week":       h.get("weekDate", ""),
                            "lowerPct":   h.get("lowerPct", 0),
                            "equalPct":   h.get("equalPct", 0),
                            "higherPct":  h.get("higherPct", 0),
                        }
                        for h in hist
                    ],
                    "pairwise": detail.get("byPack", []),
                })
                print(f"  ✓ pricing/{cat_id}/{slug}.json")
                ok += 1
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                print(f"  ✗ pricing detail {slug} : {e}", file=sys.stderr)
                failed += 1

        # ── Quality overview ──────────────────────────────────────────────
        quality_rows = []
        try:
            raw = get("/monthly-analysis-quality", {"categoryId": cat_id})
            for r in as_list(raw):
                quality_rows.append({
                    "slug":             slugify(r.get("brand", "")),
                    "brandName":        r.get("brand", ""),
                    "name":             r.get("brand", ""),
                    "articlesAnalysed": r.get("analysed", 0),
                    "qualityScore":     r.get("score", 0),
                })
            quality_rows.sort(key=lambda x: x["qualityScore"], reverse=True)
            overview_out = [{k: v for k, v in r.items() if k != "brandName"} for r in quality_rows]
            write_json(OUT_DIR / "quality" / f"{cat_id}.json", overview_out)
            print(f"  ✓ quality/{cat_id}.json ({len(quality_rows)} enseignes)")
            ok += 1
        except Exception as e:
            print(f"  ✗ quality overview : {e}", file=sys.stderr)
            failed += 1

        # ── Quality detail par enseigne ───────────────────────────────────
        for row in quality_rows:
            slug = row["slug"]
            try:
                detail = get("/monthly-analysis-quality/detail", {
                    "categoryId": cat_id,
                    "brand":      row["brandName"],
                })
                # criteriaGrades : transforme [{criterion, dist}] → {criterion: dist}
                criteria_raw = detail.get("criteria", [])
                criteria_grades = {c["criterion"]: c["dist"] for c in criteria_raw} if criteria_raw else {}

                write_json(OUT_DIR / "quality" / cat_id / f"{slug}.json", {
                    "slug":             slug,
                    "name":             row["name"],
                    "articlesAnalysed": detail.get("analysed", row["articlesAnalysed"]),
                    "qualityScore":     detail.get("score", row["qualityScore"]),
                    "globalGrades":     detail.get("globalDist", {}),
                    "criteriaGrades":   criteria_grades,
                })
                print(f"  ✓ quality/{cat_id}/{slug}.json")
                ok += 1
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                print(f"  ✗ quality detail {slug} : {e}", file=sys.stderr)
                failed += 1

        # ── Catalogue par pack ────────────────────────────────────────────
        for i, pack in enumerate(packs):
            try:
                data = get("/monthly-analysis-catalogue", {
                    "categoryId": cat_id,
                    "pack":       pack,
                })
                write_json(OUT_DIR / "catalogue" / cat_id / f"{i}.json", {
                    "packName":       pack,
                    "totalArticles":  data.get("totalArticles", 0),
                    "topSellersCount":data.get("topSellers", 0),
                    "topPct":         data.get("topPct", 0),
                    "midPct":         data.get("middlePct", 0),
                    "lowPct":         data.get("lowPct", 0),
                    "ranking":        data.get("rows", []),
                })
                print(f"  ✓ catalogue/{cat_id}/{i}.json ({pack})")
                ok += 1
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                print(f"  ✗ catalogue {pack} : {e}", file=sys.stderr)
                failed += 1

        print()

    # ── categories.json ───────────────────────────────────────────────────
    write_json(OUT_DIR / "categories.json", [
        {
            "id":        cat["id"],
            "name":      cat["name"],
            "companies": companies_by_cat.get(cat["id"], []),
            "packs":     cat["packs"],
        }
        for cat in CATEGORIES
    ])
    print(f"✓ categories.json ({len(CATEGORIES)} catégories)")

    print(f"\n{ok} succès, {failed} échec(s)")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
