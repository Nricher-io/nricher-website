# Moteur de génération — Weekly KPIs nricher

Génère des pages HTML "Weekly KPIs" reproduisant fidèlement le rendu réel de
la page app nricher (`/historical-pricing/weekly-kpis`), à partir de données
déjà calculées récupérées sur l'API nricher.

Voir `../handoff-dev/WEEKLY_KPIS_APP_SOURCE_OF_TRUTH.md` pour la référence
visuelle complète et le contrat exact de l'API (c'est le document qui prime
en cas de doute sur une couleur, une échelle ou un comportement).

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# puis renseigner NRICHER_API_TOKEN dans .env (token par entreprise, page
# "APIs" de l'administration nricher) — .env n'est jamais commité.
```

## Utilisation

```bash
# Récupère les données en direct sur l'API et génère la page
python3 generate_report.py --company-id 11

# Historique plus long pour le graphique de tendance (défaut: 13 semaines)
python3 generate_report.py --company-id 11 --weeks 26

# Tester le rendu sans token, avec le JSON d'exemple local
python3 generate_report.py --data data/_sample_api_response.json
```

Les pages générées arrivent dans `output/`, un fichier HTML autonome par
entreprise (pas de dépendance externe à part les polices Fontshare et
Chart.js, chargées en ligne).

## Structure du projet

```
nricher-engine/
├── .env.example                      ← copier en .env, jamais commité
├── data/
│   └── _sample_api_response.json     ← fixture locale (forme reelle de l'API), pour tester sans token
├── templates/
│   └── report_template.html          ← template Jinja2, theme sombre identique a l'app
├── output/                           ← pages generees (cree automatiquement)
├── generate_report.py                ← fetch API + calcul geometrie SVG + rendu
└── requirements.txt
```

## D'où viennent les données

`generate_report.py` appelle `GET /v1/weekly-kpis/:companyId` (voir
`fetch_weekly_kpis()`), qui renvoie un JSON déjà entièrement calculé côté
nricher : deltas, distributions en %, verdict généré. Ce moteur n'a **aucune
logique métier à réimplémenter** — il ne calcule que la géométrie SVG pure
(position d'aiguille de jauge, segments de donut) à partir des valeurs
brutes, exactement comme l'app le fait elle-même côté client.

`data/_sample_api_response.json` reproduit la forme exacte de cette réponse
pour permettre de tester localement sans token ni accès réseau — ce n'est
pas un modèle à remplir à la main, juste une fixture de test.

## Sécurité — token API

Le token (`NRICHER_API_TOKEN`) donne accès aux vraies données d'une
entreprise cliente. Il vit uniquement dans `nricher-engine/.env` (gitignored,
voir `.env.example` pour le format) et ne doit **jamais** être écrit en clair
dans un fichier versionné, un commit, ou collé dans une conversation.

## ⚠️ Avant d'ajouter un vrai client

Ne génère une page avec les vraies données d'un client nricher sous contrat
que si son accord explicite (et celui de nricher) a été obtenu. Pour les
entreprises simplement scrapées comme données de marché (benchmark
concurrentiel), pas de souci : c'est de la donnée publique, exactement ce
que nricher traite déjà pour son propre service.

## `generate_index.py` — découverte des entreprises

`generate_index.py` (page de recherche d'entreprises) complète
`data/companies.json` en appelant `GET /v1/companies` (JWT site, header
`Authorization: Bearer ...`, voir `NRICHER_SITE_TOKEN` dans `.env.example`) :
toute entreprise avec `weeklyKpisEnabled: true` absente de la liste y est
ajoutée automatiquement (jamais de suppression). Sans token ou si l'appel
échoue, `companies.json` reste inchangé — pas de plantage, juste un message
console.

Ça répondait au besoin décrit dans
`../handoff-dev/SITE_REQUEST_companies_list_endpoint.md` (résolu, endpoint
disponible côté app).
