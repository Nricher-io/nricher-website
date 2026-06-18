#!/usr/bin/env python3
"""
sync_reports.py
================

Publie les rapports valides sur le site : copie chaque brouillon present
dans output/<slug>.html (genere par generate_report.py) vers ../rapports/
a la racine du site, puis regenere les pages de recherche pour que le
bouton de chaque entreprise dans recherche.html devienne cliquable.

C'est l'etape manuelle de "publication" : tant qu'un rapport n'est pas
passe par ce script, il reste un brouillon local (visible uniquement dans
nricher-engine/output/), invisible et non lie depuis le site.

USAGE
-----
    python3 sync_reports.py                # publie tous les brouillons
    python3 sync_reports.py --only demostore   # publie une seule entreprise
"""

import argparse
import shutil
from pathlib import Path

import generate_index

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
RAPPORTS_DIR = BASE_DIR.parent / "rapports"


def main():
    parser = argparse.ArgumentParser(description="Publie les rapports generes vers le site (../rapports/).")
    parser.add_argument("--only", help="Slug d'une seule entreprise a publier (ex: demostore)")
    args = parser.parse_args()

    drafts = [p for p in sorted(OUTPUT_DIR.glob("*.html")) if p.stem != "index"]
    if args.only:
        drafts = [p for p in drafts if p.stem == args.only]
        if not drafts:
            print(f"Aucun brouillon trouve pour '{args.only}' dans {OUTPUT_DIR}/")
            return

    if not drafts:
        print(f"Aucun brouillon a publier dans {OUTPUT_DIR}/")
        return

    RAPPORTS_DIR.mkdir(exist_ok=True)
    for draft in drafts:
        dest = RAPPORTS_DIR / draft.name
        shutil.copyfile(draft, dest)
        print(f"  publie : {draft.name} -> {dest}")

    print(f"\n{len(drafts)} rapport(s) publie(s) dans {RAPPORTS_DIR}/")

    print("\nRegeneration des pages de recherche...")
    generate_index.main()


if __name__ == "__main__":
    main()
