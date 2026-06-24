# Weekly KPIs — reproduire la vraie page de l'app (pas l'ancien mockup)

## 0. Ce document remplace la direction de `README.md` pour ce chantier

`README.md`, `exemple_rapport.html`, `template_source.html` et `schema_donnees.json` dans
ce même dossier ont été écrits dans l'autre sens : ils décrivaient le mockup marketing
**pour aider à construire la page dans l'app**. C'est fait — la page existe dans l'app
nricher (`/historical-pricing/weekly-kpis`) et a évolué depuis ce mockup (thème sombre
uniquement, jauges sur une échelle différente, donut/courbes via une lib de charts, etc.).

**Nouvelle direction demandée par le client : c'est maintenant l'app qui est la référence
visuelle, et le site doit reproduire exactement son rendu**, alimenté par une vraie API.
Ignore les couleurs/échelles/composants SVG de l'ancien README pour cette page — ils sont
dépassés. Tout ce qu'il faut pour reproduire fidèlement le rendu réel est ci-dessous, extrait
directement du code source de l'app (pas estimé visuellement).

`generate_report.py` + `report_template.html` + `_schema_reference.json` (dans
`nricher-engine/`) sont eux aussi construits pour l'ancien design (échelle de jauge 90-120,
donut 3 couleurs plates, thème clair) et doivent être adaptés en suivant ce document — pas
réutilisés tels quels.

## 1. Source des données — nouvel endpoint API

L'app expose maintenant un endpoint public (token par entreprise, même mécanisme que les
endpoints `/v1/pricing/:companyId` et `/v1/catalog/:companyId` existants) qui renvoie tout
ce qu'il faut pour remplir une page, déjà calculé (deltas, distributions, verdict généré) :

```
GET https://api.nricher.io/v1/weekly-kpis/:companyId?token=<token>&weeks=13
```

- `companyId` : identifiant numérique nricher de l'entreprise.
- `token` : le token API en clair de l'entreprise (`CompanySettings.companyApiTokenPlain`
  côté nricher — généré depuis la page "APIs" de l'administration nricher). Un token par
  entreprise, à stocker côté site comme n'importe quel autre secret de config.
- `weeks` (optionnel, défaut 13, 1-104) : nombre de semaines d'historique pour le graphique
  de tendance. La table de priorité peut renvoyer moins de lignes que `weeks` si
  l'entreprise n'a pas encore assez d'historique de snapshots — ce n'est pas un bug à
  corriger côté site, juste l'état réel des données.
- En local (dev), `http://localhost:8081/v1/weekly-kpis/:companyId?token=...`.

Pas d'auth JWT, pas de header — uniquement ce `token` en query param, comme les autres
endpoints publics `/v1/*`.

### Forme de la réponse (exemple réel, tronqué)

```json
{
  "company": { "id": 11, "name": "Nedgis" },
  "generatedAt": "2026-06-24T13:32:02.173Z",
  "creationDate": "2026-06-24T05:06:09.932Z",
  "week": 26,
  "prevWeek": 25,
  "prevWeekLabel": "S25",
  "competitorCount": 17,
  "hero": {
    "articlesAnalysed": 27110,
    "articlesAnalysedDelta": { "text": "+3 %", "down": false, "good": false },
    "articlesMatched": 8036,
    "priceIndexGlobal": 108,
    "priceIndexGlobalDelta": { "text": "-9 pts", "down": true, "good": true }
  },
  "gauges": [
    { "key": "ALL", "label": "Price Index All", "value": 102, "previousValue": 109, "delta": { "text": "-7 pts", "down": true, "good": true } },
    { "key": "1P_MIN", "label": "Price Index 1P min", "value": 108, "previousValue": 117, "delta": { "text": "-9 pts", "down": true, "good": true } },
    { "key": "3P_MIN", "label": "3P Price Min", "value": null, "previousValue": null, "delta": null },
    { "key": "3P_SAME_MIN", "label": "3P same min", "value": null, "previousValue": null, "delta": null }
  ],
  "priorityTable": [
    { "week": 26, "isCurrent": true, "top": 105, "middle": 106, "low": 107, "allAvgMin1P": 108, "allAvgMin3P": null }
  ],
  "trendChart": {
    "weeks": ["31 mars", "07 avr.", "...", "23 juin"],
    "priceIndex1P": [107, 107, "...", 115],
    "priceIndex3P": [null, null, "...", null]
  },
  "attractivenessStacked": [
    { "week": "31 mars", "lowerPct": 34.8, "equalPct": 20.9, "higherPct": 44.4 }
  ],
  "competitors": {
    "table": [
      { "name": "Andlight", "articlesAll": 4080, "piAll": 107, "articlesMin": 2727, "piMin": 109, "gt100": 1593, "eq100": 508, "lt100": 627, "pi1pMin": 109, "art1pMin": 2727 }
    ],
    "stacked": [
      { "name": "Andlight", "matched": 2727, "lowerPct": 23, "equalPct": 19, "higherPct": 58, "pi": 109 }
    ]
  },
  "sellers": {
    "table": [
      { "name": "nedgis", "analysed": 27110, "matched": 8036, "piMin": 108, "gt100": 4432, "eq100": 1310, "lt100": 2295 }
    ],
    "stacked": [
      { "name": "nedgis", "matched": 8036, "lowerPct": 29, "equalPct": 16, "higherPct": 55, "pi": 108 }
    ]
  },
  "categoryStacked": [
    { "name": "suspension", "count": 2791, "lowerPct": 24, "equalPct": 17, "higherPct": 59, "pi": 111 }
  ],
  "verdict": {
    "headline": "Le repricing porte ses fruits — l'indice recule de 2 pts vs la semaine précédente.",
    "figures": [
      { "value": "-2 pts", "label": "indice global vs S25", "good": true },
      { "value": "+2 pts", "label": "d'articles moins chers vs S25", "good": true },
      { "value": "0", "label": "vendeurs plus compétitifs que vous", "good": true },
      { "value": "8036", "label": "articles suivis en continu", "good": null }
    ]
  }
}
```

Tout est déjà calculé côté API (deltas, `good`/`down`, distributions en %, verdict généré).
Le site n'a **aucune logique métier à réimplémenter** — uniquement de la mise en forme et,
pour 2 composants graphiques précis (jauges, donut), de la géométrie SVG pure (voir section
4). `value: null` = donnée non disponible pour cette entreprise (ex: pas de vendeurs 3P) :
afficher `—`, ne pas masquer la carte/ligne.

## 2. Design tokens réels de l'app (thème sombre uniquement — pas de mode clair)

```css
/* Fond / cartes / texte — variables CSS réelles de l'app (format oklch, valide en CSS direct) */
--background: oklch(0.145 0 0);
--foreground: oklch(0.985 0 0);
--card: oklch(0.205 0 0);
--card-foreground: oklch(0.985 0 0);
--muted-foreground: oklch(0.708 0 0);
--border: oklch(1 0 0 / 10%);     /* = ring-foreground/10, le contour des cartes */
--radius: 0.625rem;               /* base — les cartes utilisent rounded-xl (~0.75rem) */

/* Couleur de marque nricher */
--custom-green: #59efbd;          /* accent positif (verdict, tagline "vous êtes moins cher") */

/* Couleurs de statut Price Index — PAS de palier orange/jaune intermédiaire dans les CHIFFRES,
   uniquement dans le DÉGRADÉ visuel des jauges (voir section 4a) */
--cheaper: #10b981;   /* PI < 100 */
--equal:   #3b82f6;   /* PI = 100 */
--pricier: #ef4444;   /* PI > 100 */

/* Texte conditionnel (classes Tailwind réelles, équivalent CSS direct) */
/* PI > 100 -> rouge: light #dc2626 / dark #f87171 */
/* PI < 100 -> vert:  light #16a34a / dark #4ade80 */
/* PI = 100 -> bleu:  light #2563eb / dark #60a5fa */
```

**Polices** (chargées via Fontshare, exactement comme dans l'app) :

```html
<link rel="preconnect" href="https://api.fontshare.com">
<style>
@import url('https://api.fontshare.com/v2/css?f[]=clash-display@500,600,700&f[]=satoshi@400,500,700,900&display=swap');
</style>
```

```css
--wk-font-display: 'Clash Display', 'Syne', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
--wk-font-body:    'Satoshi', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
```

`--wk-font-display` = titres, gros chiffres (hero, jauges, valeurs PI). `--wk-font-body` =
tout le reste (paragraphes, libellés, tooltips).

**Carte de base** (`ReportCard`, le composant que tout le reste utilise) :
- fond `var(--card)`, texte `var(--card-foreground)`, contour 1px `var(--border)`,
  `border-radius: 12px` (`rounded-xl`), padding vertical `16px`.
- une barre fine en haut de la carte, `height: 2px` (jauges : `3px`), couleur `#3b82f6`
  (bleu-500), pleine largeur — visible sur quasiment toutes les cartes sauf les cartes de
  table (compétiteurs/vendeurs/catégories, voir section 4e) qui n'ont pas de barre.
- au survol : `transform: translateY(-4px)` + ombre portée plus marquée, transition fluide
  (~300ms, easing standard).

## 3. Anatomie de la page (ordre réel, `WeeklyKpisLayout.tsx`)

1. **Header** — badge entreprise, badge `WEEKLY KPIS · SEMAINE {n} · PRICE INDEX`, titre
   H1 "Le marché a bougé. {tagline}" (tagline colorée vert si l'indice baisse, rouge s'il
   monte, neutre si stable), sous-titre "`{articlesAnalysed}` articles analysés cette
   semaine sur `{competitorCount}` concurrents directs."
2. **4 cartes hero-stats** (grid 2 colonnes mobile / 4 desktop) : Articles analysés (+ delta
   % vs semaine précédente), Matchés concurrence, Price Index global (+ flèche ▲/▼ rouge/
   verte + valeur S-1), Mise à jour (date/heure).
3. **3 jauges** Price Index : `ALL` (toutes offres), `1P_MIN` (meilleure offre propre),
   `3P_MIN` (meilleure offre marché) — voir section 4a pour la géométrie exacte. (`3P_SAME_MIN`
   existe dans la donnée mais n'est pas affiché en jauge dans l'app — uniquement dans le
   payload API pour usage futur.)
4. **Tendance** (2 cartes côte à côte) : graphique en courbes indice prix 1P/3P dans le
   temps (ligne pointillée de référence à 100), + graphique en aires empilées
   moins cher/aligné/plus cher (%) dans le temps. Voir section 4c.
5. **Table priorité commerciale** (si données dispo) : une ligne par semaine, colonnes
   Top sales / Middle sales / Low sales (chips colorés par sévérité PI) / All (1P + 3P).
6. **Vue d'ensemble** (2 cartes côte à côte) : donut répartition moyenne tous concurrents
   (section 4b) + classement à barres horizontales du plus compétitif au plus cher (10
   premiers, triés par PI croissant).
7. **Face aux concurrents** : une ligne par concurrent (12 premiers, triés par volume) —
   barre empilée lower/equal/higher % + PI à droite. Voir section 4d (`DistributionRow`).
8. **Competitor analysis** : table détaillée par concurrent (articles all/min, PI all/min,
   répartition >100/=100/<100 en nombre d'articles, pas en %).
9. **Vendeurs** : même table détaillée + même vue répartition % (`DistributionRow`) que les
   concurrents, pour les vendeurs (sellers) plutôt que les enseignes concurrentes.
10. **Catégories** (si données dispo) : même vue répartition % (`DistributionRow`) par
    catégorie produit, avec le volume affiché à gauche du PI.
11. **Verdict** — carte de conclusion, bordure teintée vert (`border-custom-green/30`),
    titre généré (`verdict.headline`), 4 chiffres clés séparés par des traits verticaux
    (`verdict.figures`, couleur verte si `good !== false`, rouge si `good === false`).

## 4. Mécaniques visuelles exactes

### 4a. Jauges Price Index

Jauge semi-circulaire SVG, `viewBox="0 0 200 116"`, centre `(100, 100)`, rayon `80`.
**Échelle 80 (gauche) → 120 (droite)** — pas 90-120, c'est la valeur mise à jour de l'app.

```js
const CX = 100, CY = 100, R = 80
const polar = (r, deg) => {
  const rad = deg * Math.PI / 180
  return { x: CX + r * Math.cos(rad), y: CY - r * Math.sin(rad) }
}
const angleOf = (value, min = 80, max = 120) => {
  const t = Math.min(Math.max((value - min) / (max - min), 0), 1)
  return 180 * (1 - t)              // 180° = tout à gauche (min), 0° = tout à droite (max)
}
const needle = polar(R * 0.76, angleOf(value))   // extrémité de l'aiguille
```

- Arc de fond : un seul `<path>` allant de 180° à 0° (demi-cercle), `stroke-width: 12`,
  `stroke-linecap: round`, rempli par un **dégradé linéaire 5 stops** (pas 3 couleurs
  plates) : `0% cheaper(#10b981) → 30% #84cc16 → 55% #f59e0b → 78% #f97316 → 100%
  pricier(#ef4444)`.
- Aiguille : `<line x1="100" y1="100" x2={needle.x} y2={needle.y} stroke-width="3"
  stroke-linecap="round">` + `<circle cx="100" cy="100" r="6">`, couleur = `piHex(value)`
  (vert si <100, bleu si =100, rouge si >100 — **3 couleurs**, pas le dégradé).
- Sous l'arc : grosse valeur centrale (police display, couleur = règle de sévérité PI) +
  badge delta (vert/rouge selon `delta.good`).
- Sous la valeur : une **barre de progression linéaire** (même dégradé 5 stops que l'arc,
  horizontale cette fois), avec un repère blanc vertical fin à la position de la semaine
  précédente (`reference`) et un rond plein à la position de la valeur actuelle. Labels
  `80` / `120` aux extrémités, `S{n} : {valeur}` au centre.
- **"Ghost number"** : la valeur en très grand (police display, ~96px), positionnée en
  fond à droite de la carte, `opacity: 0.10`, couleur = `piHex(value)`, `z-index` derrière
  le contenu, `pointer-events: none`.
- Toute la carte est dans un tooltip au survol : `"{delta.text} vs {prevWeekLabel} :
  {previousValue}"` (ex: `"-9 pts vs S25 : 117"`).
- Si `value === null` : aiguille au centre (90° = position neutre), grande valeur affiche
  `—`, pas de delta, pas de tooltip, ghost number masqué.

### 4b. Donut "répartition moyenne"

Donut SVG, anneau (pas un camembert plein) — `innerRadius` ≈ 62% du rayon externe,
petit espace entre segments (`padAngle` ≈ 1.5°), coins légèrement arrondis. 3 segments :
`cheaper` (#10b981, "Moins cher"), `equal` (#3b82f6, "Aligné"), `pricier` (#ef4444, "Plus
cher"), valeurs = `avgLower` / `avgEqual` / `avgHigher` (somme = 100). Label `{valeur}%`
en blanc dans chaque segment si la part est suffisamment grande pour ne pas être tronquée.
Au centre du donut : la valeur "Plus cher" en gros (couleur pricier) + "plus cher" en
petit dessous. Légende sous le donut : 3 puces colorées + libellé + valeur.

Si tu pars de la fonction Python `compute_donut_segments` déjà présente dans
`generate_report.py`, elle reste utilisable quasi telle quelle pour générer les
coordonnées d'arc SVG — change uniquement les 3 couleurs (`var(--good)/--blue/--bad` →
`#10b981/#3b82f6/#ef4444`) et ajoute le label central. La géométrie exacte d'un anneau
Nivo (vs un disque plein) n'a pas besoin d'être reproduite au pixel : un anneau SVG
classique (cercle stroke au lieu de path plein) donne un résultat visuellement équivalent.

### 4c. Graphiques de tendance

Deux courbes/aires sur fond `var(--card)`, sans grille verticale (grille horizontale fine
en pointillés, couleur `var(--border)`), légende cliquable au-dessus (puce couleur +
libellé, grisée si la série est masquée).

- **Indice prix (1P/3P)** : 2 courbes, couleurs `#f59e0b` (1P) et `#14b8a6` (3P), courbe
  lissée (interpolation monotone, pas linéaire droite), ligne de référence pointillée
  horizontale à `y = 100`. Si une seule courbe a des données (l'autre est tout `null`),
  elle est mise en valeur avec un remplissage en dégradé (couleur de la courbe → transparent)
  sous la ligne. Points visibles si ≤ 14 points de données.
- **Attractivité (%)** : 3 aires **empilées** (cheaper/equal/pricier, mêmes 3 couleurs
  qu'ailleurs), opacité ~0.85, axe Y fixe 0-100, labels `{valeur}%` sur les points, libellés
  de légende `Moins cher / Aligné / Plus cher`.
- Survol : tooltip vertical (ligne pointillée + carte flottante) montrant la date complète
  et la valeur de chaque série visible à ce point.
- Vu que le site n'a pas de lib de charts React (Nivo) : **Chart.js** (léger, vanilla JS,
  pas de build step) reproduit ce rendu sans problème — `type: 'line'`, `tension` pour la
  courbe lissée, `fill` + `stacked: true` pour le graphique d'attractivité, un plugin
  d'annotation ou une simple ligne dessinée à la main pour la référence à 100.

### 4d. Lignes de répartition (`DistributionRow` — concurrents/vendeurs/catégories)

Chaque ligne : libellé (largeur fixe, tronqué si trop long) + une **barre horizontale en 3
segments collés** (lower/equal/higher, mêmes 3 couleurs, largeur = leur %, texte blanc `{n}%`
affiché dans le segment seulement si ≥ 9%) + le PI à droite (couleur de sévérité). Au survol
d'un segment : il s'agrandit légèrement (`scaleY(1.1)`, `brightness(1.1)`) et un tooltip
affiche `"{libellé} — {nom du segment} : {valeur}%"`.

### 4e. Tables détaillées (competitor/seller analysis)

Tables HTML classiques, pas de carte de couleur — en-têtes alignés à droite pour les
colonnes numériques, centrés pour les colonnes PI. Les valeurs PI sont affichées dans un
petit "chip" arrondi (fond pastel : vert clair si <100, bleu clair si =100, rouge clair si
>100 — même règle de sévérité, fond à 15% d'opacité de la couleur).

### 4f. Carte verdict

Carte avec bordure teintée verte (`border-color: rgba(89, 239, 189, 0.3)`), pas de barre
en haut. Badge "CE QUE NRICHER VOIT QUE VOUS NE VOYEZ PAS ENCORE" en haut, qui dépasse
légèrement le bord supérieur de la carte (`margin-top` négatif). Titre généré
(`verdict.headline`) en gros, police display. 4 chiffres clés côte à côte séparés par un
trait vertical fin, chaque chiffre coloré vert si `good !== false`, rouge si
`good === false` (donc `good: null` → vert, comme un chiffre neutre informatif).

## 5. Comportements interactifs à reproduire

- Toutes les cartes (jauges, hero-stats, carte verdict) se soulèvent légèrement au survol
  (`translateY(-4px)`, ombre plus marquée), transition fluide.
- Tooltips au survol : jauges (delta vs semaine précédente), segments de barres
  (concurrents/vendeurs/catégories/attractivité), chips de la table priorité (valeur
  exacte), barres du classement par indice prix.
- Segments/barres de classement : léger agrandissement + éclaircissement au survol.

## 6. Pour rappel — décisions déjà actées côté nricher (app + API)

- L'API renvoie du JSON déjà calculé et propre, **pas** de géométrie SVG pré-calculée
  (pas de `needle_x`/`needle_y`/`dasharray`/etc. dans la réponse) — c'est au site de
  calculer ça à l'affichage à partir de `value`, exactement comme l'app le fait elle-même
  (voir section 4a). Donc oui, les fonctions `compute_gauge_needle` /
  `compute_gauge_bar_pct` de `generate_report.py` sont toujours la bonne approche — il
  faut juste les recaler sur l'échelle 80-120 et le nouveau dégradé (section 4a), pas les
  supprimer.
- Aucun champ couleur d'entreprise (`meta.company_color`) n'existe dans cette API — ça
  reste un réglage propre au site (sa propre config de branding par client), indépendant
  des données nricher.
- Aucun champ de texte bilingue `{fr, en}` n'existe dans cette API — tout le texte généré
  (`verdict.headline`, `hero.title`, etc. côté app) est en français uniquement pour
  l'instant. Si le site a besoin d'anglais, c'est à traduire côté site (comme le reste du
  site, via son propre système i18n), pas un champ à attendre de l'API.
