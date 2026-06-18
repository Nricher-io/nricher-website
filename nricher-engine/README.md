# Moteur de génération — Weekly KPIs nricher

Génère automatiquement des pages HTML "Weekly KPIs" dans la charte graphique
réelle de nricher.io, à partir de fichiers de données JSON.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
# Une seule entreprise
python3 generate_report.py --data data/exemple_fictif_demostore.json

# Toutes les entreprises d'un coup
python3 generate_report.py --data "data/*.json"
```

Les pages générées arrivent dans `output/`, un fichier HTML autonome par
entreprise (pas de dépendance externe à part les polices Fontshare chargées
en ligne).

## Structure du projet

```
nricher-engine/
├── data/                       ← un fichier JSON par entreprise
│   ├── _schema_reference.json  ← documentation du format attendu (ignoré par le script)
│   └── exemple_fictif_demostore.json
├── templates/
│   └── report_template.html    ← template Jinja2, dérivé de la vraie DA nricher.io
├── output/                     ← pages générées (créé automatiquement)
├── generate_report.py
└── requirements.txt
```

## Format des données

Voir `data/_schema_reference.json` pour le détail complet de chaque champ.
Le point important : `meta.source_label` est **obligatoire**, et s'affiche
en bandeau sur la page elle-même. Il doit dire honnêtement d'où vient la
donnée (ex. `"Donnée publique scrapée — pas un client nricher"` ou,
le jour où c'est légitime, le statut réel de la donnée pour un client sous
contrat).

Le graphique de tendance (`trend_chart`) ne demande que des valeurs brutes
(`price_index_3p: [108, 107, 106, ...]`) — le script calcule lui-même
l'échelle et les coordonnées SVG, pas besoin de positionner les points à la
main.

## Brancher une vraie source de données

Ce moteur est volontairement agnostique de la source. Il ne fait QUE :
lire un JSON → remplir le template → écrire un HTML.

Pour connecter une vraie source, il suffit d'écrire un petit script qui
PRODUIT un JSON conforme au schéma, par exemple :

```python
# exemple : adapter.py — à écrire le jour où l'accès est confirmé
import json

def fetch_from_nricher_api(company_id, api_token):
    """Appelle l'API officielle nricher et reconstruit le JSON attendu."""
    # ... appel HTTP réel à l'API documentée ...
    return {
        "meta": {...},
        "hero": {...},
        # etc.
    }

data = fetch_from_nricher_api("conforama", api_token="...")
with open("data/conforama.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

Puis lancer `generate_report.py` normalement. Aucune modification du
template ni du moteur n'est nécessaire.

Trois sources possibles, à choisir selon ce qui est confirmé en interne :
1. **API REST officielle** de nricher (si elle existe et qu'un token est
   fourni) — la plus propre.
2. **Export SFTP / Excel partagé** que nricher fournit déjà à ses clients
   pour alimenter leurs outils tiers — lire le fichier avec `pandas` ou
   `openpyxl` et le reformater en JSON.
3. **Scraping web public** des catalogues des marques cibles (la même
   méthode que nricher utilise lui-même) — pour les entreprises qui ne
   sont pas clientes et n'ont donc aucune donnée dans l'outil interne.

## ⚠️ Avant d'ajouter un vrai client

Ne génère une page avec les vraies données d'un client nricher sous contrat
que si son accord explicite (et celui de nricher) a été obtenu. Pour les
250 entreprises qui sont simplement scrapées comme données de marché
(benchmark concurrentiel), pas de souci : c'est de la donnée publique,
exactement ce que nricher traite déjà pour son propre service.
