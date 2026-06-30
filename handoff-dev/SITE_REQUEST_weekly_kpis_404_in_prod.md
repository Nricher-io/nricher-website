# Demande côté site — GET /v1/weekly-kpis/:companyId renvoie 404 en prod

Sens site → app/API, comme `SITE_REQUEST_companies_list_endpoint.md`. À relayer à qui
s'occupe du backend nricher (ou à la session Claude Code sur `nricher-workspace`).

## Contexte — ce qui vient de se passer

Le job planifié `weekly-kpis-refresh.yml` (refresh hebdomadaire des 136 rapports) était
bloqué depuis sa mise en place par `GET /v1/companies` qui n'existait pas (voir
`SITE_REQUEST_companies_list_endpoint.md`). Cet endpoint est maintenant livré et
**fonctionne correctement en prod** : le dernier run a bien récupéré la liste des 133
entreprises `weeklyKpisEnabled=true`, avec leurs `id`, et a réussi à minter un token par
entreprise via `POST /v1/:companyId/create-api-token` pour chacune (les 133 mints ont
réussi, aucune erreur à cette étape).

**Mais l'étape suivante échoue systématiquement** : l'appel `GET
/v1/weekly-kpis/:companyId?token=...&weeks=13` qui doit suivre renvoie **404 Not Found**,
pour **les 133 entreprises sans exception** — y compris pour des entreprises qui ont déjà
servi de cas de test fonctionnels par le passé (Nedgis id=11, Conforama id=1, Simplybearings
id=204).

## Le détail exact de l'échec (run GitHub Actions du 2026-06-30T11:22Z)

```
GET https://api.nricher.io/v1/weekly-kpis/11?token=***&weeks=13
404 Client Error: Not Found

0 réussie(s), 133 échec(s) sur 133 entreprise(s)
```

(le token a été retiré du message ci-dessus avant de le coller ici — voir le correctif
de sécurité fait côté site en parallèle de cette demande : les tokens par-entreprise ne
doivent plus jamais apparaître en clair dans un message d'erreur/log)

Le **même call** (même path, même mécanisme de token, même query params) est documenté
comme fonctionnel dans `handoff-dev/WEEKLY_KPIS_APP_SOURCE_OF_TRUTH.md` (section 1, qui
décrit cet endpoint comme déjà en prod et utilisé pour générer les rapports affichés sur
le site). Le code site (`generate_report.py::fetch_weekly_kpis`) n'a pas changé depuis
que cet endpoint fonctionnait.

## Hypothèses, à vérifier côté backend

Comme **les 133 appels échouent de façon identique** (pas quelques entreprises isolées
sans snapshot calculé — ce qui serait attendu et pas un bug), ça pointe vers un problème
de route/déploiement plutôt qu'un problème de données par entreprise :

1. **L'endpoint n'est peut-être pas déployé sur `https://api.nricher.io` (prod)** — testé
   et fonctionnel seulement en local (`localhost:8081`) ou sur un autre environnement.
2. **Régression récente** sur le routing prod (ex: changement de path, de version d'API,
   middleware qui intercepte avant la route).
3. **Le `companyId` utilisé n'est pas le bon identifiant** côté prod — à vérifier si l'API
   `/v1/companies` (prod) et `/v1/weekly-kpis/:id` (prod) référencent bien le même espace
   d'ID (peu probable vu que `create-api-token` accepte ces mêmes ID sans erreur, mais à
   exclure).

## Ce qu'il faut faire

1. Reproduire en interne : `curl -X POST https://api.nricher.io/v1/11/create-api-token -H "Authorization: Bearer <NRICHER_SITE_TOKEN>"` pour avoir un token frais, puis `curl "https://api.nricher.io/v1/weekly-kpis/11?token=<token>&weeks=13"` et confirmer le 404 en direct.
2. Vérifier que la route `GET /v1/weekly-kpis/:companyId` est bien déployée sur
   l'environnement prod (pas seulement en dev/staging).
3. Si elle est déployée, vérifier les logs serveur prod au moment de l'appel pour voir si
   la requête atteint seulement un 404 générique (route inexistante) ou un 404 métier
   (« pas de snapshot pour cette entreprise ») — la distinction change tout : si c'est la
   2ᵉ option pour TOUTES les entreprises sans exception, c'est suspect aussi (calcul de
   snapshot cassé globalement ?).
4. Une fois corrigé, dis-le moi : je redéclenche le job `weekly-kpis-refresh.yml` pour
   confirmer que les 136 rapports se régénèrent et se publient correctement de bout en
   bout.

## Bloquant

Contrairement à `/v1/companies` qui n'était "pas urgent", celui-ci bloque **complètement**
le refresh automatique même maintenant que la découverte de la liste fonctionne — sans
cet endpoint, aucun rapport ne peut être régénéré du tout.
