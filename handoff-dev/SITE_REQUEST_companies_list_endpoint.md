# Demande côté site — endpoint de liste des entreprises

Sens inverse de `WEEKLY_KPIS_APP_SOURCE_OF_TRUTH.md` : ce document part du site
vers l'app/API nricher. À relayer à qui s'occupe du backend nricher (ou à la
session Claude Code sur `nricher-workspace`).

## ⚠️ Mise à jour — ce n'est plus juste "pas bloquant"

Cette demande date d'avant la mise en prod du job planifié de refresh
automatique. **Depuis, ce job échoue chaque semaine** (`.github/workflows/
weekly-kpis-refresh.yml`, tous les lundis 06:00 UTC) parce qu'il dépend de cet
endpoint pour découvrir la liste des entreprises à régénérer — voir
`generate_all_reports.py`. Le site gère maintenant l'échec proprement (message
clair dans les logs au lieu d'un crash brut), mais le refresh automatique des
136 rapports Weekly KPIs est **suspendu** tant que cet endpoint n'existe pas.

C'est aussi un prérequis pour la section 9 de
`SITE_REQUEST_monthly_analysis_page.md` (nouvelle page "Monthly Analysis" —
sans liste fiable des entreprises par catégorie, impossible de remplacer les
données fictives de cette page par les vraies données).

## Le problème

Avant le passage à l'API réelle pour Weekly KPIs, le site découvrait la liste
des entreprises (`nricher-engine/data/companies.json`, utilisée pour la barre
de recherche du site et `recherche.html`) en scannant des fichiers JSON
déposés localement (`data/<entreprise>.json`). Chaque nouveau fichier
ajoutait automatiquement l'entreprise à la liste.

Ce mécanisme n'a plus de sens : il n'y a plus de fichiers locaux, les données
viennent à la demande de `GET /v1/weekly-kpis/:companyId`. Mais cet endpoint
est **par ID** — il faut déjà connaître l'ID pour l'appeler. Il n'existe (à
notre connaissance) aucun endpoint qui liste les entreprises disponibles.

Résultat actuel : `companies.json` doit être maintenu à la main, ID par ID,
ce qui ne tiendra pas dans le temps si le nombre de clients Weekly KPIs
augmente — et empêche toute automatisation (le job planifié ne peut tout
simplement rien découvrir tout seul).

## Ce qui serait utile

Un endpoint qui liste les entreprises pour lesquelles le site peut générer un
rapport :

```
GET https://api.nricher.io/v1/companies
Authorization: Bearer <NRICHER_SITE_TOKEN>

[
  { "id": 11, "name": "Nedgis", "weeklyKpisEnabled": true },
  { "id": 42, "name": "Andlight", "weeklyKpisEnabled": false }
]
```

### Auth — déjà résolu, pas un point ouvert

Le site a déjà un JWT de niveau "site" (`NRICHER_SITE_TOKEN`, dans
`nricher-engine/.env`, jamais commité) qui est **déjà accepté** par un
endpoint admin existant côté nricher :

```
POST /v1/:companyId/create-api-token
Authorization: Bearer <NRICHER_SITE_TOKEN>
```

(voir `nricher-engine/generate_report.py::create_company_token`, utilisé pour
minter à la volée un token par-entreprise). Ce JWT site permet déjà d'agir
sur n'importe quelle entreprise par ID — il n'y a donc pas besoin d'un
nouveau mécanisme d'auth : **`GET /v1/companies` devrait accepter exactement
le même `Authorization: Bearer <NRICHER_SITE_TOKEN>`**, avec la même
vérification que `create-api-token` fait déjà côté backend. Le site appelle
cet endpoint avec un header `Authorization`, pas un `?token=` en query param
(correction par rapport à une version précédente de ce document).

### Champs attendus

- `id` (number) — identifiant nricher de l'entreprise, utilisé ensuite pour
  `POST /v1/:id/create-api-token` puis `GET /v1/weekly-kpis/:id`.
- `name` (string) — nom affiché.
- `weeklyKpisEnabled` (bool) — le site filtre déjà sur ce champ côté client
  (`generate_all_reports.py` : `[c for c in response.json() if
  c.get("weeklyKpisEnabled")]`) ; évite de tenter de générer un rapport pour
  une entreprise qui n'a pas la donnée. Si un champ équivalent existe déjà
  sous un autre nom côté nricher, le site s'adapte — donner le nom exact.
- **Pagination** : probablement pas nécessaire au volume actuel (~136
  entreprises), mais à signaler si la liste devient grande.

## Qui consomme cet endpoint, côté site (pour vérifier la forme exacte)

- `nricher-engine/generate_all_reports.py` — refresh hebdomadaire automatique
  (le job qui échoue actuellement), génère TOUS les rapports `weeklyKpisEnabled=true`.
- `nricher-engine/generate_index.py::fetch_companies_from_api()` — tient à
  jour `data/companies.json` (liste affichée dans la barre de recherche du
  site), dégradé déjà géré si l'appel échoue.

## Pas urgent dans l'absolu, mais bloque une automatisation déjà en place

Le flux manuel (`generate_report.py --company-id 11`, etc.) fonctionne très
bien pour les quelques clients déjà connus — ce n'est pas la prod qui est en
danger. Mais le job planifié hebdomadaire échoue concrètement chaque lundi
depuis sa mise en place, et restera rouge jusqu'à ce que cet endpoint existe.
