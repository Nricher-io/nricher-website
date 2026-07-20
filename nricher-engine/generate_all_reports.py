#!/usr/bin/env python3
"""
generate_all_reports.py
========================

Génère les pages Weekly KPIs pour TOUTES les entreprises avec
weeklyKpisEnabled=true. Deux sources possibles pour la liste :

1. GET /v1/companies (endpoint API nricher) — utilisé en priorité.
2. data/weekly_companies.json — repli local si l'API échoue.
   Format : [{"id": 11, "name": "Nedgis", "weeklyKpisEnabled": true}, ...]

Pensé pour être lancé par un job planifié
(voir .github/workflows/weekly-kpis-refresh.yml) — l'échec d'une entreprise
(ex: pas encore de snapshot calculé côté nricher) n'interrompt pas les autres.

USAGE
-----
    python3 generate_all_reports.py
    python3 generate_all_reports.py --weeks 26
"""

import argparse
import json
import sys
from pathlib import Path

import requests

import generate_report as gr

FALLBACK_JSON = Path(__file__).parent / "data" / "weekly_companies.json"


def load_companies_from_api(base_url, jwt_token):
    response = requests.get(
        f"{base_url}/v1/companies",
        headers={"Authorization": f"Bearer {jwt_token}"},
        timeout=15,
    )
    response.raise_for_status()
    return [c for c in response.json() if c.get("weeklyKpisEnabled")]


def load_companies_from_fallback():
    if not FALLBACK_JSON.exists():
        return None
    with open(FALLBACK_JSON, encoding="utf-8") as f:
        data = json.load(f)
    # Ignorer les entrées placeholder (id null)
    return [c for c in data if c.get("weeklyKpisEnabled") and c.get("id") is not None]


def main():
    parser = argparse.ArgumentParser(
        description="Génère les pages Weekly KPIs pour toutes les entreprises weeklyKpisEnabled=true."
    )
    parser.add_argument("--weeks", type=int, default=13, help="Semaines d'historique (défaut 13).")
    args = parser.parse_args()

    try:
        base_url, jwt_token = gr.get_site_jwt_and_base_url()
    except RuntimeError as e:
        print(f"Configuration manquante : {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Essai via l'API
    companies = None
    try:
        companies = load_companies_from_api(base_url, jwt_token)
        print(f"API /v1/companies OK — {len(companies)} entreprise(s) weeklyKpisEnabled")
    except requests.RequestException as e:
        print(f"GET /v1/companies a échoué ({e}) — tentative repli JSON...", file=sys.stderr)

    # 2. Repli local si l'API a échoué
    if companies is None:
        companies = load_companies_from_fallback()
        if companies:
            print(f"Repli JSON OK — {len(companies)} entreprise(s) dans {FALLBACK_JSON}")
        else:
            print(
                f"Ni l'API ni le repli JSON ({FALLBACK_JSON}) ne fournissent de liste.\n"
                "Renseigner nricher-engine/data/weekly_companies.json avec les IDs des\n"
                "entreprises weeklyKpisEnabled=true pour activer la génération automatique.",
                file=sys.stderr,
            )
            sys.exit(1)

    if not companies:
        print("Aucune entreprise weeklyKpisEnabled=true disponible.", file=sys.stderr)
        sys.exit(1)

    gr.OUTPUT_DIR.mkdir(exist_ok=True)
    env = gr.build_environment()

    ok, failed = [], []
    for c in companies:
        try:
            data = gr.fetch_weekly_kpis(c["id"], weeks=args.weeks)
            out_path = gr.render_report(data, env)
            ok.append((c["name"], out_path))
        except Exception as e:
            failed.append((c["name"], str(e)))

    print(f"\n{len(ok)} réussie(s), {len(failed)} échec(s) sur {len(companies)} entreprise(s)\n")
    for name, path in ok:
        print(f"  OK  {name:30s} -> {path}")
    for name, err in failed:
        print(f"  X   {name:30s} : {err}", file=sys.stderr)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()