# Demande côté site — nouvelle page "Monthly Analysis" dans l'app

Même sens que `README.md` (site → app) : le site a construit le design d'une nouvelle
fonctionnalité, jamais encore présente dans l'app, et ce document sert de référence pour
la reproduire à l'identique côté app nricher. À relayer à qui s'occupe du front app (ou à
la session Claude Code sur `nricher-workspace`).

## 0. Contexte

Le site marketing nricher.io a une nouvelle section "Analyse de marché" : pour chacun des
3 piliers produit (**Pricing**, **Quality**, **Catalogue**), on choisit une catégorie de
marché (ex: "Sport & Outdoor") et on obtient une fiche qui compare entre elles toutes les
enseignes suivies dans cette catégorie.

**Objectif de cette demande** : ajouter l'équivalent dans l'app, sous l'onglet
**Historical Pricing**, comme une nouvelle page **"Monthly Analysis"** positionnée
**juste en dessous de "Weekly KPIs"** dans la nav (même niveau, même style de nav item).
Design strictement identique à ce qui existe déjà sur le site — voir section 2.

**Pas de connexion aux vraies données pour cette étape.** Le site utilise pour l'instant
des données 100% fictives, générées par une formule déterministe (détaillée en section 8)
uniquement pour avoir un rendu visuel crédible. Cette demande ne porte que sur la
reproduction de l'UI/UX. La connexion aux vraies données (agrégation par catégorie de
marché côté nricher) fera l'objet d'une **deuxième demande séparée**, une fois cette page
posée — voir section 9 pour ce que ça impliquera côté API.

## 1. Où l'intégrer

Dans l'app, `Historical Pricing` contient déjà `Weekly KPIs`
(`packages/web/src/views/apps/historical-pricing/weekly-kpis/`). Ajouter à côté un dossier
frère `monthly-analysis/` avec une nouvelle entrée de nav **sous** Weekly KPIs, qui ouvre la
page "Monthly Analysis". Cette page contient 3 onglets/piliers : **Pricing**, **Quality**,
**Catalogue** (mêmes 3 noms que les sous-items du menu "Analyse" du site).

## 2. Référence visuelle (fichiers fournis dans ce dossier)

Ces 4 fichiers sont des **copies exactes** des pages du site, à la date de cette demande —
ce sont à la fois la référence visuelle pixel-perfect (ouvrir directement dans un
navigateur, double-clic) et la référence de code source exacte (CSS, structure, JS) :

| Fichier | Pilier |
|---|---|
| `analyse-pricing.html` | Pricing — tableau récap + fiche détail par enseigne |
| `analyse-quality.html` | Quality — tableau récap + fiche détail par enseigne |
| `analyse-catalogue.html` | Catalogue — donut + classement, avec swipe entre "packs" |
| `analyse-categories.js` | Mapping catégorie → enseignes (la même donnée que la nav de catégories des 3 pages ci-dessus) |

Ouvrir chaque page, sélectionner une catégorie (ex: "Sport & Outdoor") pour voir le rendu
complet. Pour Pricing/Quality, cliquer ensuite une ligne du tableau pour voir la fiche
détail par enseigne.

Ces pages utilisent les design tokens nricher déjà documentés dans `README.md` (section 2
de ce même dossier) — mêmes couleurs `--mint`/`--blue`/`--good`/`--bad`, même typo
Clash Display / Satoshi, même rayon de pilule `--r-pill`. Pas besoin de les redéfinir,
sauf les nouvelles couleurs spécifiques à cette page listées en section 10.

## 3. Anatomie commune aux 3 piliers — sélecteur de catégorie

Avant d'arriver à un rapport, l'utilisateur choisit une catégorie de marché :

- Un champ de recherche texte (placeholder "Sport, Maison, Beauté…") qui filtre en direct
  une grille de cartes catégorie.
- Chaque carte catégorie affiche : nom de la catégorie + "{N} enseignes suivies".
- Cliquer une carte affiche le rapport du pilier (sections 4/5/6) juste en dessous, avec un
  scroll fluide vers cette zone. La carte sélectionnée reste visuellement marquée
  (bordure mint + ombre).

Cette grille + recherche est strictement la même UI sur les 3 piliers (voir `#catGrid`,
`#catSearch`, `.an-cat-card` dans le code source des 3 fichiers).

## 4. Pilier Pricing

**Niveau 1 — récap.** Un tableau listant **toutes** les enseignes de la catégorie
sélectionnée, triées par Price Index croissant (la moins chère en haut) :

| Enseigne | Articles analysés | Articles matchés | Price Index 1P | (chevron) |
|---|---|---|---|---|

- Pastille colorée sur le PI : **verte** (`--good`) si PI ≤ 100, **rouge** (`--bad`) si > 100.
- Chaque ligne est cliquable (curseur pointer, fond qui se teinte au survol) et affiche à
  droite un petit bouton "Voir le détail ›" qui se colore en bleu/mint au survol — c'est
  l'indice visuel que la ligne est cliquable, à ne pas oublier.

**Niveau 2 — détail par enseigne** (clic sur une ligne) :
- En-tête : nom de l'enseigne + pastille "PI {valeur}" (même couleur good/bad) + 2 badges
  "{N} articles analysés" / "{N} articles matchés".
- **"Price index evolution"** : graphique en courbes, une courbe par **concurrent** de la
  catégorie (pas l'enseigne elle-même), sur 6 points temporels, + une ligne pointillée de
  référence à 100. Légende centrée, couleurs de courbe variées (palette ronde, pas de
  règle good/bad ici, juste des couleurs distinctes par concurrent).
- **"Price attractivity evolution"** : aire empilée à 100%, 3 séries **Cheaper / Aligned /
  Pricier** (vert `--good` / bleu `--blue` / rouge `--bad`), mêmes 6 points temporels.
- **"Pricing analysis"** : une barre horizontale empilée par concurrent — 3 segments
  **Lower % / Equal % / Higher %** (mêmes 3 couleurs), avec le PI du concurrent affiché à
  droite (coloré good/bad). Légende des 3 couleurs centrée au-dessus de la liste.

## 5. Pilier Quality

**Niveau 1 — récap.** Tableau listant toutes les enseignes de la catégorie, triées par
**note qualité décroissante** (la meilleure en haut) :

| Enseigne | Note qualité (pastille "{score} / 100") | (chevron) |
|---|---|---|

- Pastille à 3 tons (pas good/bad comme Pricing, ici 3 niveaux) :
  **bleu** (`--blue`) si score ≥ 70, **gris neutre** (`#4b5563`) si 40-69, **rouge**
  (`--bad`) si < 40.
- Même bouton "Voir le détail ›" qu'en Pricing.

**Niveau 2 — détail par enseigne** (clic sur une ligne) :
- En-tête : nom de l'enseigne + badge "{N} articles analysées".
- Label "average grade" (en vert mint, minuscules) + grosse pastille "{score} / 100" (même
  charte 3 tons que ci-dessus).
- **"global grade - % of articles"** : **une seule** barre horizontale empilée, répartie en
  **7 segments** A+/A/B/C/D/E/F (voir couleurs exactes section 10) — la répartition note de
  l'ensemble du catalogue de cette enseigne.
- **"distribution of articles by criteria - % of articles"** : 4 lignes, une par critère
  **Title / Image / Video / Description**, chacune une barre 7 segments (même palette) —
  la répartition de notes spécifique à ce critère. Important : dans les données mockées,
  le critère **Video** est volontairement tiré vers les mauvaises notes (souvent
  100% E/F) — c'est un constat réel du produit (la vidéo est rarement renseignée par les
  enseignes), pas un bug du générateur de données fictives.
- Légende des 7 couleurs (points colorés + nom de grade) centrée sous les barres.

## 6. Pilier Catalogue

Pas de tableau récap ici — sélectionner une catégorie affiche directement la fiche.

- Badge "Exemple — données fictives" (à retirer une fois connecté aux vraies données).
- "{N} articles en vente" en gros, au-dessus du donut.
- **Donut** à 3 segments **Top sellers / Middle sellers / Low sellers** (mint `#60efbe` /
  bleu `#2e58ca` / gris `#cbd5e1`), avec au centre le nombre de "Top sellers" et légende
  des 3 parts en %, sous le donut.
- **Classement** à droite : une barre horizontale par enseigne, montrant
  "{compte} / {total top sellers}" à l'intérieur de la barre, colorée selon un dégradé de
  rang (vert → rouge, palette à 10 niveaux, section 10), plus un badge "+{X}%" ("potentiel
  de CA supplémentaire") à droite de chaque barre.
- **Navigation par "packs"** — particularité de ce pilier : chaque catégorie contient
  plusieurs **sous-catégories produit** ("packs", ex. pour Bricolage & Jardin :
  "Climatiseur & Ventilateur", "Salon de jardin", "Barbecue"). Une barre au-dessus du
  rapport affiche le nom du pack courant, entourée de 2 flèches (‹ ›) et suivie de points
  cliquables (un par pack) sous le badge. Le contenu (donut + classement) change avec une
  petite transition de fondu (~130ms) en changeant de pack. Navigable aussi par **swipe**
  tactile/souris (seuil ~50px horizontal) sur toute la zone du rapport. Flèches désactivées
  en butée (premier/dernier pack). Voir `goToPack()` / `renderPackChrome()` dans
  `analyse-catalogue.html` pour le détail exact du comportement.

## 7. Taxonomie des catégories (donnée actuelle — approximative)

`analyse-categories.js` contient la liste exacte utilisée aujourd'hui par le site : **8
catégories**, construites à la main à partir des enseignes qui ont effectivement des
données Weekly KPIs (celles sans données ont été retirées), plafonnées à 10 enseignes max
par catégorie. Chaque catégorie a aussi 2-3 "packs" (sous-catégories produit, pilier
Catalogue uniquement) inventés à la main pour l'instant.

**Cette taxonomie est volontairement approximative** — elle a été construite sans accès à
la vraie hiérarchie produit nricher. Si l'app a déjà une notion de catégorie de marché plus
fiable (basée sur les vraies données catalogue), elle devrait primer sur ce fichier dès que
disponible — voir section 9.

## 8. Données mockées pour l'instant — formule exacte (à reproduire si besoin)

Tant que les vraies données ne sont pas branchées, le site génère des nombres fictifs mais
**stables** (même catégorie/enseigne → toujours les mêmes chiffres, pas aléatoire à chaque
rendu) via un PRNG seedé par une chaîne de caractères. Si l'app a besoin de la même
stabilité visuelle pendant le développement (avant le branchement réel), voici l'algorithme
exact (identique sur les 3 pages, copier directement) :

```js
function seedFromString(str) {
  var h = 0;
  for (var i = 0; i < str.length; i++) { h = (h * 31 + str.charCodeAt(i)) | 0; }
  return h;
}
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
```

Chaque métrique a sa propre seed string (ex: `cat.id + '::' + brand + '::overview'`,
`cat.id + '::' + company + '::' + competitor + '::trend'`...) — voir le détail dans le
script de chaque page (`buildOverviewRow`, `buildPairwise`, `buildTrend`,
`buildAttractiveness` pour Pricing ; `buildGradeDist` pour Quality ; `buildMockReport` pour
Catalogue). Pas besoin de comprendre chaque formule en détail si l'app préfère générer ses
propres données fictives différemment — l'important est juste qu'elles soient **stables**
pour ne pas donner l'impression d'un bug pendant les démos/QA.

## 9. Connexion aux vraies données (phase 2, plus tard — pas dans cette demande)

Pas à traiter maintenant, juste pour anticiper : pour remplacer les données fictives, il
faudra côté nricher un moyen d'agréger, **par catégorie de marché et par enseigne** :
- Pricing : PI 1P courant + historique (réutilise probablement la même donnée que
  `/v1/weekly-kpis/:companyId`, mais agrégée pour plusieurs enseignes à la fois plutôt
  qu'une seule).
- Quality : un score de qualité de fiche produit + répartition par critère
  (Title/Image/Video/Description) — à confirmer si cette donnée existe déjà ailleurs dans
  l'app (mentionné comme "Bien présenté" sur le site) ou si elle doit être créée.
- Catalogue : répartition top/middle/low sellers + nombre d'articles par catégorie.

Et surtout : une vraie notion de **catégorie de marché** régulièrement par enseigne (pour
remplacer `analyse-categories.js`, section 7). Cette partie fera l'objet d'une demande
séparée une fois la page posée et validée côté UI.

## 10. Design tokens spécifiques à cette page

En plus des tokens déjà connus (`README.md` section 2), cette page introduit :

```css
/* Pricing — pastille PI (2 tons, identique à la regle good/bad existante) */
--good: #1fae7a;  /* PI <= 100 */
--bad:  #e2452f;  /* PI > 100 */

/* Quality — pastille score (3 tons) */
--blue: #2e58ca;  /* score >= 70 */
--neu:  #4b5563;  /* 40 <= score < 70 */
--bad:  #e2452f;  /* score < 40 */

/* Quality — 7 grades, du meilleur au pire (utilisé pour les barres empilées) */
A+ : #3b82f6
A  : #2e58ca
B  : #1e3a6e
C  : #6b7280
D  : #f87171
E  : #dc2626
F  : #7f1d1d

/* Catalogue — donut */
Top sellers    : #60efbe (mint)
Middle sellers : #2e58ca (blue)
Low sellers    : #cbd5e1 (gris clair)

/* Catalogue — degrade de rang classement (10 niveaux, vert -> rouge) */
['#1fae7a', '#47b668', '#6fbe56', '#9ac34a', '#cec24c',
 '#ffc04d', '#f7a443', '#f0893a', '#e96735', '#e2452f']
```

## 11. Marche à suivre pour l'intégration

1. Ouvrir les 3 fichiers `.html` fournis dans un navigateur, à côté de l'écran où tu codes.
2. Construire d'abord le sélecteur de catégorie (section 3), commun aux 3 piliers — c'est
   la même structure partout, donc probablement un seul composant réutilisable.
3. Construire chaque pilier dans son propre composant (sections 4/5/6), en réutilisant les
   valeurs CSS exactes trouvées dans le `<style>` de chaque fichier source (classes
   préfixées `.pr-*` pour Pricing, `.ql-*` pour Quality, `.cat-*` pour Catalogue — pas de
   collision entre elles, chaque fichier les définit dans son propre `<style>`).
4. Pour l'instant, alimenter avec des données fictives (section 8, ou votre propre
   générateur si plus simple côté app) — ne pas bloquer sur la vraie donnée.
5. Vérifier au fur et à mesure contre le rendu des fichiers `.html` fournis : couleurs des
   pastilles aux seuils exacts (PI 100, score 70 et 40), comportement du swipe/flèches en
   butée sur Catalogue, légende des 7 grades en Quality.
6. Une fois l'UI validée, ouvrir la discussion sur la section 9 (vraies données) comme
   chantier séparé.
