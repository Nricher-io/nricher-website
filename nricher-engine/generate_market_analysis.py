#!/usr/bin/env python3
"""
generate_market_analysis.py  (v2)
====================================

Génère les JSON statiques pour les 3 pages d'analyse de marché (Pricing,
Quality, Catalogue). Utilise les vrais endpoints nricher v1 avec le même
pattern d'auth que generate_report.py : site token → mint company token →
?token=xxx.

Endpoints utilisés :
  GET  /v1/companies                                 liste entreprises
  POST /v1/:id/create-api-token                      mint token (jamais stocké)
  GET  /v1/categories/:id?token=xxx                  catégories + enseignes + subCategories
  GET  /v1/weekly-kpis/:id?token=xxx&weeks=N         PI courant + semaines + attractivité
  GET  /v1/pricing/:id?token=xxx&searchAfter=xxx     pricing paginé
  GET  /v1/competitor-trends/:id?token=xxx&weeks=N   historique PI/concurrent (optionnel)
  GET  /v1/quality/:id?token=xxx&searchAfter=xxx     scores qualité paginés (optionnel)
  GET  /v1/catalog/:id?token=xxx&searchAfter=xxx     catalogue paginé

Les endpoints optionnels (competitor-trends, quality) sont ignorés si le
serveur répond 404 — le script génère quand même les fichiers disponibles
et remplit les champs manquants avec des valeurs neutres.

USAGE
-----
    python3 generate_market_analysis.py
"""

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import median

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os

BASE_URL = os.getenv("NRICHER_API_BASE_URL", "https://api.nricher.io")
SITE_TOKEN = os.getenv("NRICHER_SITE_TOKEN", "")
OUT_DIR = Path(__file__).parent.parent / "data" / "market-analysis"

# Grading scale (quality-filters.service.ts)
GRADE_SCALE = [
    ("Aplus", 0.95), ("A", 0.85), ("B", 0.75),
    ("C", 0.60),     ("D", 0.50), ("E", 0.40), ("F", 0.0),
]

REQUEST_DELAY = 0.3  # secondes entre pages paginées


# ── Auth ──────────────────────────────────────────────────────────────────────

def _site_headers():
    return {"Authorization": f"Bearer {SITE_TOKEN}"}


def mint_token(company_id):
    """Mint un token frais par entreprise (écrase l'existant — usage immédiat uniquement)."""
    resp = requests.post(
        f"{BASE_URL}/v1/{company_id}/create-api-token",
        headers=_site_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["companyApiToken"]


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _scrub(msg):
    """Retire les valeurs token=xxx des messages d'erreur avant logging."""
    return re.sub(r"token=[^&\s\"']+", "token=***", str(msg))


def fetch_all_pages(company_id, path, extra_params=None):
    """Parcourt toutes les pages searchAfter et retourne la liste data fusionnée."""
    token = mint_token(company_id)
    params = {"token": token, **(extra_params or {})}
    rows = []
    while True:
        try:
            resp = requests.get(
                f"{BASE_URL}{path}/{company_id}",
                params=params, timeout=60,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise requests.RequestException(_scrub(e)) from None
        body = resp.json()
        page = body.get("data", [])
        rows.extend(page)
        sa = body.get("searchAfter")
        if not sa or not page:
            break
        params["searchAfter"] = sa
        time.sleep(REQUEST_DELAY)
    return rows


def fetch_once(company_id, path, extra_params=None):
    """GET unique (endpoints non paginés)."""
    token = mint_token(company_id)
    params = {"token": token, **(extra_params or {})}
    try:
        resp = requests.get(
            f"{BASE_URL}{path}/{company_id}",
            params=params, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise requests.RequestException(_scrub(e)) from None


# ── Utilitaires ───────────────────────────────────────────────────────────────

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


def to_grade(value):
    if value is None:
        return "F"
    for grade, threshold in GRADE_SCALE:
        if value >= threshold:
            return grade
    return "F"


def grade_dist(values):
    """Liste de flottants 0-1 → distribution de grades en %."""
    counts = {g: 0 for g, _ in GRADE_SCALE}
    for v in values:
        counts[to_grade(v if v <= 1 else v / 100)] += 1
    total = len(values) or 1
    return {g: round(c / total * 100) for g, c in counts.items()}


_GRADE_LABEL_MAP = {"A+": "Aplus", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "F": "F"}


def grade_dist_from_labels(labels):
    """Liste de chaînes 'A+','A','B'... → distribution en % (normalise A+ → Aplus)."""
    counts = {g: 0 for g, _ in GRADE_SCALE}
    for lbl in labels:
        counts[_GRADE_LABEL_MAP.get(lbl or "F", "F")] += 1
    total = len(labels) or 1
    return {g: round(c / total * 100) for g, c in counts.items()}


def _in_cat(row, cat_name):
    return row.get("CATEGORY_FINAL") == cat_name or row.get("CATEGORY") == cat_name


def _in_pack(row, pack_name):
    return (
        row.get("CATEGORY_FINAL") == pack_name
        or row.get("LEVEL_3") == pack_name
        or row.get("LEVEL_4") == pack_name
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not SITE_TOKEN:
        print("NRICHER_SITE_TOKEN manquant.", file=sys.stderr)
        sys.exit(1)

    print(f"API  : {BASE_URL}")
    print(f"Vers : {OUT_DIR}\n")

    # ── 1. Liste des entreprises ──────────────────────────────────────────────
    try:
        resp = requests.get(
            f"{BASE_URL}/v1/companies",
            headers=_site_headers(), timeout=15,
        )
        resp.raise_for_status()
        all_companies = resp.json()
    except requests.RequestException as e:
        print(f"ERREUR /v1/companies : {e}", file=sys.stderr)
        sys.exit(1)

    print(f"{len(all_companies)} entreprise(s) trouvée(s)\n")

    def cslug(c):
        return slugify(c.get("slug") or c.get("name", ""))

    # ── 2. Carte des catégories (appel /v1/categories par entreprise) ─────────
    cat_map = {}   # cat_id → {id, name, _slugs (set), _pack_seen (set), packs ([]}

    for co in all_companies:
        try:
            body = fetch_once(co["id"], "/v1/categories")
            # Accepte {data: [...]} ou un tableau direct
            cats = body if isinstance(body, list) else body.get("data", [])
        except requests.RequestException as e:
            print(f"  ✗ categories {cslug(co)} : {e}", file=sys.stderr)
            continue

        for cat in cats:
            cat_name = cat.get("category", "")
            cat_id = slugify(cat_name)
            if not cat_id:
                continue
            if cat_id not in cat_map:
                cat_map[cat_id] = {
                    "id": cat_id, "name": cat_name,
                    "_companies": {},   # slug → name
                    "_pack_seen": set(), "packs": [],
                }
            entry = cat_map[cat_id]
            slug = cslug(co)
            entry["_companies"][slug] = co.get("name", "")

            # subCategories si l'endpoint est mis à jour, sinon gammes non-1P/3P
            for sc in cat.get("subCategories", []):
                if sc and sc not in entry["_pack_seen"]:
                    entry["packs"].append(sc)
                    entry["_pack_seen"].add(sc)
            for sc in cat.get("gammes", []):
                if sc and sc not in ("1P", "3P") and sc not in entry["_pack_seen"]:
                    entry["packs"].append(sc)
                    entry["_pack_seen"].add(sc)

        time.sleep(0.1)

    categories = [
        {
            "id": e["id"], "name": e["name"],
            "companies": [{"slug": s, "name": n} for s, n in e["_companies"].items()],
            "packs": e["packs"],
        }
        for e in cat_map.values()
    ]
    write_json(OUT_DIR / "categories.json", categories)
    print(f"✓ categories.json ({len(categories)} catégories)\n")

    # Accumulateurs cross-entreprise
    # cat_id → comp_name → {pi_values, matched}
    pricing_overview_acc = defaultdict(lambda: defaultdict(lambda: {"pi_values": [], "matched": 0}))
    # cat_id → pack_name → {all_eans, top_eans, co_top: {slug → {name, count}}}
    catalogue_acc = defaultdict(lambda: defaultdict(lambda: {
        "all_eans": set(), "top_eans": set(), "co_top": {},
    }))

    ok = failed = 0

    # ── 3. Données par entreprise ─────────────────────────────────────────────
    for co in all_companies:
        cid = co["id"]
        slug = cslug(co)
        name = co.get("name", "")

        co_cats = [c for c in categories if any(x["slug"] == slug for x in c["companies"])]
        if not co_cats:
            continue

        print(f"[{slug}] {name}")

        # Weekly KPIs
        kpi = {}
        current_pi = None
        trend_weeks = []
        try:
            kpi = fetch_once(cid, "/v1/weekly-kpis", {"weeks": 13})
            current_pi = kpi.get("hero", {}).get("priceIndexGlobal")
            trend_weeks = kpi.get("trendChart", {}).get("weeks", [])
            ok += 1
        except requests.RequestException as e:
            print(f"  ✗ weekly-kpis : {e}", file=sys.stderr)
            failed += 1

        # Pricing (paginé)
        pricing_rows = []
        try:
            pricing_rows = fetch_all_pages(cid, "/v1/pricing")
            ok += 1
        except requests.RequestException as e:
            print(f"  ✗ pricing : {e}", file=sys.stderr)
            failed += 1

        # Competitor trends — optionnel (nouveau endpoint)
        comp_trends = {}
        try:
            td = fetch_once(cid, "/v1/competitor-trends", {"weeks": 13})
            trend_weeks = td.get("weeks", trend_weeks)
            comp_trends = {c["name"]: c["piHistory"] for c in td.get("competitors", [])}
        except requests.RequestException:
            pass   # pas encore déployé — fallback ci-dessous

        # Quality — optionnel (nouveau endpoint, paginé)
        quality_rows = []
        try:
            quality_rows = fetch_all_pages(cid, "/v1/quality")
        except requests.RequestException:
            pass

        # Catalog (paginé)
        catalog_rows = []
        try:
            catalog_rows = fetch_all_pages(cid, "/v1/catalog")
            ok += 1
        except requests.RequestException as e:
            print(f"  ✗ catalog : {e}", file=sys.stderr)
            failed += 1

        # ── Fichiers par catégorie ────────────────────────────────────────
        for cat in co_cats:
            cat_id = cat["id"]
            cat_name = cat["name"]
            packs = cat.get("packs", [])

            cat_pricing = [r for r in pricing_rows if _in_cat(r, cat_name)]
            cat_quality  = [r for r in quality_rows  if _in_cat(r, cat_name)]
            cat_catalog  = [r for r in catalog_rows  if _in_cat(r, cat_name)]

            # Accumulation pour pricing overview
            for r in cat_pricing:
                comp = r.get("COMPETITOR", "")
                my_p = r.get("MY_PRICE") or 0
                co_p = r.get("COMPET_PRICE") or 0
                if comp and my_p and co_p:
                    # PI du concurrent relatif à nous : COMPET_PRICE/MY_PRICE×100
                    pricing_overview_acc[cat_id][comp]["pi_values"].append(co_p / my_p * 100)
                    pricing_overview_acc[cat_id][comp]["matched"] += 1

            # Pairwise PI par pack
            pairwise = []
            for pack in packs:
                pack_rows = [r for r in cat_pricing if _in_pack(r, pack)]
                if pack_rows:
                    pis = [
                        r["MY_PRICE"] / r["COMPET_PRICE"] * 100
                        for r in pack_rows
                        if (r.get("MY_PRICE") or 0) and (r.get("COMPET_PRICE") or 0)
                    ]
                    pi_val = round(median(pis)) if pis else None
                    n = len(pack_rows)
                    lower  = round(sum(1 for r in pack_rows if (r.get("MY_PRICE") or 0) < (r.get("COMPET_PRICE") or 1)) / n * 100)
                    equal  = round(sum(1 for r in pack_rows if r.get("MY_PRICE") == r.get("COMPET_PRICE")) / n * 100)
                    higher = max(0, 100 - lower - equal)
                else:
                    pi_val = lower = equal = higher = None
                pairwise.append({
                    "pack": pack, "priceIndex": pi_val,
                    "lowerPct": lower or 0, "equalPct": equal or 0, "higherPct": higher or 0,
                })

            # competitorTrends : nouveau endpoint ou fallback snapshot hebdo
            if comp_trends:
                trends_list = [{"name": n, "piHistory": h} for n, h in comp_trends.items()]
            else:
                trends_list = [
                    {"name": c.get("name", ""), "piHistory": [c.get("pi")]}
                    for c in kpi.get("competitors", {}).get("stacked", [])[:15]
                ]

            # pricing/<catId>/<slug>.json
            write_json(OUT_DIR / "pricing" / cat_id / f"{slug}.json", {
                "slug": slug, "name": name,
                "priceIndex": current_pi,
                "weeks": trend_weeks,
                "competitorTrends": trends_list,
                "attractiveness": [
                    {"week": r.get("week"), "lowerPct": r.get("lowerPct", 0),
                     "equalPct": r.get("equalPct", 0), "higherPct": r.get("higherPct", 0)}
                    for r in kpi.get("attractivenessStacked", [])
                ],
                "pairwise": pairwise,
            })
            print(f"  ✓ pricing/{cat_id}/{slug}.json")
            ok += 1

            # quality/<catId>/<slug>.json (si données dispo)
            if cat_quality:
                total_q = len(cat_quality)
                # Utilise les grades pré-calculés si présents dans la réponse API
                has_labels = bool(cat_quality[0].get("NRICHER_GRADE"))
                if has_labels:
                    q_score = round(
                        sum(r.get("NRICHER_RATING") or 0 for r in cat_quality) / total_q * 100
                    )
                    global_grades = grade_dist_from_labels(
                        [r.get("NRICHER_GRADE", "F") for r in cat_quality]
                    )
                    criteria = {
                        "Titre":       grade_dist_from_labels([r.get("TITLE_GRADE", "F") for r in cat_quality]),
                        "Image":       grade_dist_from_labels([r.get("IMAGE_GRADE", "F") for r in cat_quality]),
                        "Vidéo":       grade_dist_from_labels([r.get("VIDEO_GRADE", "F") for r in cat_quality]),
                        "Description": grade_dist_from_labels([r.get("DESC_GRADE", "F") for r in cat_quality]),
                    }
                else:
                    nr = [r.get("NRICHER_RATING") or 0 for r in cat_quality]
                    q_score = round(sum(nr) / total_q * 100) if nr else 0
                    global_grades = grade_dist(nr)
                    criteria = {
                        "Titre":       grade_dist([r.get("TITLE_RATING") or 0 for r in cat_quality]),
                        "Image":       grade_dist([r.get("IMAGE_FILLING") or 0 for r in cat_quality]),
                        "Vidéo":       grade_dist([r.get("VIDEO_FILLING") or 0 for r in cat_quality]),
                        "Description": grade_dist([r.get("DESC_RATING")   or 0 for r in cat_quality]),
                    }
                write_json(OUT_DIR / "quality" / cat_id / f"{slug}.json", {
                    "slug": slug, "name": name,
                    "articlesAnalysed": total_q,
                    "qualityScore": q_score,
                    "globalGrades": global_grades,
                    "criteriaGrades": criteria,
                })
                print(f"  ✓ quality/{cat_id}/{slug}.json")
                ok += 1

            # Accumulation catalogue
            for pack in packs:
                pack_rows = [r for r in cat_catalog if _in_pack(r, pack)]
                b = catalogue_acc[cat_id][pack]
                for r in pack_rows:
                    ean = r.get("EAN", "")
                    if ean:
                        b["all_eans"].add(ean)
                        if r.get("PRIO") == "Top":
                            b["top_eans"].add(ean)
                if slug not in b["co_top"]:
                    b["co_top"][slug] = {"name": name, "count": 0}
                b["co_top"][slug]["count"] += sum(1 for r in pack_rows if r.get("PRIO") == "Top")

    # ── 4. pricing/<catId>.json (overview concurrents) ────────────────────────
    for cat in categories:
        cat_id = cat["id"]
        acc = pricing_overview_acc.get(cat_id, {})
        if not acc:
            continue
        total_matched = sum(d["matched"] for d in acc.values()) or 1
        overview = []
        for comp_name, d in acc.items():
            pis = d["pi_values"]
            overview.append({
                "slug": slugify(comp_name), "name": comp_name,
                "articlesAnalysed": total_matched,
                "articlesMatched": d["matched"],
                "priceIndex": round(median(pis)) if pis else None,
            })
        overview.sort(key=lambda x: (x["priceIndex"] is None, x["priceIndex"] or 0))
        write_json(OUT_DIR / "pricing" / f"{cat_id}.json", overview)
        print(f"✓ pricing/{cat_id}.json ({len(overview)} concurrents)")
        ok += 1

    # ── 5. quality/<catId>.json (overview) ────────────────────────────────────
    for cat in categories:
        cat_id = cat["id"]
        q_dir = OUT_DIR / "quality" / cat_id
        if not q_dir.exists():
            continue
        overview = []
        for f in sorted(q_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                overview.append({
                    "slug": d["slug"], "name": d["name"],
                    "articlesAnalysed": d.get("articlesAnalysed", 0),
                    "qualityScore": d.get("qualityScore", 0),
                })
            except Exception:
                pass
        overview.sort(key=lambda x: x["qualityScore"], reverse=True)
        if overview:
            write_json(OUT_DIR / "quality" / f"{cat_id}.json", overview)
            print(f"✓ quality/{cat_id}.json ({len(overview)} enseignes)")
            ok += 1

    # ── 6. catalogue/<catId>/<i>.json ─────────────────────────────────────────
    for cat in categories:
        cat_id = cat["id"]
        for i, pack in enumerate(cat.get("packs", [])):
            b = catalogue_acc[cat_id].get(pack, {})
            all_eans = b.get("all_eans", set())
            top_eans = b.get("top_eans", set())
            co_top   = b.get("co_top", {})
            total = len(all_eans)
            if not total:
                continue
            top_count = len(top_eans)
            top_pct = round(top_count / total * 100)
            ranking = []
            for s, d in co_top.items():
                n_top = d["count"]
                potential = max(0, round((1 - n_top / top_count) * 100)) if top_count else 100
                ranking.append({
                    "slug": s, "name": d["name"],
                    "topSellerArticles": n_top,
                    "potentialPct": potential,
                })
            ranking.sort(key=lambda x: x["topSellerArticles"], reverse=True)
            write_json(OUT_DIR / "catalogue" / cat_id / f"{i}.json", {
                "packName": pack,
                "totalArticles": total,
                "topPct": top_pct,
                "midPct": max(0, 100 - top_pct),
                "lowPct": 0,
                "topSellersCount": top_count,
                "ranking": ranking,
            })
            print(f"✓ catalogue/{cat_id}/{i}.json ({pack})")
            ok += 1

    print(f"\n{ok} succès, {failed} échec(s)")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
