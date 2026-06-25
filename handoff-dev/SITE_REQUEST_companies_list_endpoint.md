# Demande côté site — endpoint de liste des entreprises

Sens inverse de `WEEKLY_KPIS_APP_SOURCE_OF_TRUTH.md` : ce document part du site
vers l'app/API nricher. À relayer à qui s'occupe du backend nricher (ou à la
session Claude Code sur `nricher-workspace`).

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
augmente.

## Ce qui serait utile

Un endpoint qui liste les entreprises pour lesquelles le site peut générer un
rapport, par exemple :

```
GET https://api.nricher.io/v1/companies?token=<token>

[
  { "id": 11, "name": "Nedgis", "weeklyKpisEnabled": true },
  { "id": 42, "name": "Andlight", "weeklyKpisEnabled": false }
]
```

Points ouverts, à trancher côté nricher (le site s'adapte à ce qui est le
plus simple à exposer) :

- **Auth** : un token par entreprise (comme `/v1/weekly-kpis/:id`) ne peut pas
  lister *toutes* les entreprises — il faudrait soit un token de niveau
  "site"/admin distinct, soit une autre forme d'authentification.
- **Filtre** : tout le monde n'a pas forcément les Weekly KPIs activés —
  un champ comme `weeklyKpisEnabled` (ou équivalent) éviterait au site
  d'essayer de générer un rapport pour une entreprise qui n'a pas la donnée.
- **Pagination** : probablement pas nécessaire au volume actuel, mais à
  signaler si la liste devient grande.

## Pas bloquant

Le flux actuel fonctionne très bien pour les quelques clients déjà connus
(`generate_report.py --company-id 11`, etc.) — ce n'est utile que pour éviter
la maintenance manuelle à mesure que de nouveaux clients Weekly KPIs
arrivent. Aucune urgence.
