#!/usr/bin/env python3
"""
generate_all_reports.py
========================

Génère les pages Weekly KPIs pour TOUTES les entreprises avec
weeklyKpisEnabled=true (GET /v1/companies), au lieu d'une seule via
generate_report.py --company-id. Pensé pour être lancé par un job planifié
(voir .github/workflows/weekly-kpis-refresh.yml) — l'échec d'une entreprise
(ex: pas encore de snapshot calculé côté nricher) n'interrompt pas les autres.

USAGE
-----
    python3 generate_all_reports.py
    python3 generate_all_reports.py --weeks 26
"""

import argparse
import sys

import requests

import generate_report as gr


def main():
    parser = argparse.ArgumentParser(
        description="Génère les pages Weekly KPIs pour toutes les entreprises weeklyKpisEnabled=true."
    )
    parser.add_argument("--weeks", type=int, default=13, help="Semaines d'historique (défaut 13).")
    args = parser.parse_args()

    base_url, jwt_token = gr.get_site_jwt_and_base_url()
    response = requests.get(
        f"{base_url}/v1/companies",
        headers={"Authorization": f"Bearer {jwt_token}"},
        timeout=15,
    )
    response.raise_for_status()
    companies = [c for c in response.json() if c.get("weeklyKpisEnabled")]

    if not companies:
        print("Aucune entreprise weeklyKpisEnabled=true reçue depuis l'API.", file=sys.stderr)
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
        sys.exit(1)  # rien généré du tout = vrai problème ; des échecs partiels restent acceptables


if __name__ == "__main__":
    main()
