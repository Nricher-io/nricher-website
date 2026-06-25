# Demande côté site — 84 entreprises sans utilisateur lié (404 sur weekly-kpis)

Sens site → app/backend, comme `SITE_REQUEST_companies_list_endpoint.md`. À
relayer à qui s'occupe du backend nricher (ou à la session Claude Code sur
`nricher-workspace`).

## Le problème

En local, sur les 136 entreprises avec `weeklyKpisEnabled: true` (réponse de
`GET /v1/companies`), seules 52 renvoient des données sur
`GET /v1/weekly-kpis/:companyId` — les 84 autres répondent 404.

Le code exact (`packages/api/src/view-tables/weekly-kpis/service/weekly-kpis-report.service.ts`,
méthode `getReportForCompany`) montre pourquoi :

```ts
const representativeUser = await this.prisma.user.findFirst({
  where: { current_company_id: { has: companyId } },
  select: { id: true }
})

if (!representativeUser) {
  throw new NotFoundException(
    `No user found for company ID ${companyId} to resolve weekly KPIs context`
  )
}
```

Avant même de calculer quoi que ce soit, l'API a besoin d'un `User` dont
`current_company_id` contient l'entreprise, pour servir de contexte. Sans ce
lien, 404 — **indépendamment du fait que des données de pricing/snapshot
existent réellement ou non** pour cette entreprise. Exemple vérifié en
détail : `Asteri` (id=49) — 404 avec exactement ce message.

## Ce qu'il faudrait

Pour chacune des 84 entreprises listées plus bas, soit :
- lier un utilisateur existant à l'entreprise (`current_company_id` doit
  contenir son id), si un utilisateur "propriétaire" légitime existe déjà
  pour elle en base de dev ;
- soit confirmer qu'il n'y a effectivement aucun utilisateur dev pour ces
  entreprises et que c'est attendu (dans ce cas le site les ignorera
  simplement — pas de demande de création d'utilisateurs fictifs, juste un
  besoin de savoir si le trou est volontaire ou pas).

## Pas de panique côté prod (a priori)

Cette base est l'environnement de **dev local**. Si en production chaque
client a forcément un compte utilisateur pour se connecter à l'app, ce
problème ne devrait pas exister à ce niveau là-bas — mais ça vaut le coup de
le confirmer avant de considérer que ça se résoudra automatiquement.

## Liste des 84 entreprises concernées (id — nom)

```
44 — 3Suisses                  208 — alltricks                209 — alpiniste
94 — Amazon                    166 — amazon es                 167 — amazon it
124 — ambientedirect           90 — Andlight                   49 — Asteri
19 — Belong                    27 — Boticinal                  13 — Bricomarche
26 — bulgari                   155 — carrefour es               96 — CDiscount
95 — centrale du casque        122 — chiaracolombini            114 — Clarins
31 — Cocooncenter              157 — conforama es                125 — connox
32 — Dafymoto                  88 — Darty                       202 — debenhams
207 — ekosport                 131 — fermliving                 133 — finnishdesignshop
132 — flos                     103 — Fnac                       52 — Galerieslafayette
245 — glisshop                 210 — hardloop                   113 — Hermes
109 — Inside_75                246 — irun                       28 — JPG
37 — Labecanerie               134 — lamptwist                  92 — Lancome
129 — lecedrerouge             154 — leroy merlin               159 — leroy merlin es
162 — leroy merlin it          137 — light11                    48 — Lightonline
39 — Louis Moto                156 — mabeoindustries            145 — madeinbebe
149 — madeindesign de          147 — madeindesignuk              161 — maisons du monde es
164 — maisons du monde it      53 — Manomano                    158 — manomano es
163 — manomano it              15 — Manor                       153 — maxibazar
38 — Maxxess                   33 — Motoaxxe                    34 — Motoblouz
40 — Motocard                  135 — myareadesign                110 — Neuvieme_store
116 — Payot                    22 — Pharmazon                   20 — Pixmania
119 — Printemps                93 — red deco                    45 — Rue du commerce
108 — Sandro_BDV               206 — sephora                    46 — Silvera
115 — Sisley                   121 — skapetze                   130 — speedway
120 — SVR                      41 — Teamaxe                     43 — Thecoolrepublic
211 — trekkinn                 35 — Ubaldi                      140 — vertbaudet
42 — Voltex                    127 — westwing                   100 — zoomici
```

## Pas bloquant

Le site fonctionne déjà très bien pour les 52 entreprises résolues — ceci ne
fait qu'élargir la couverture. Aucune urgence, mais utile à savoir avant de
considérer la liste "complète" côté site.
