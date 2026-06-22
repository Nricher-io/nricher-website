# Weekly KPIs — handoff design & logique pour l'app nricher

Ce dossier est la référence complète pour reproduire le **front de la page "Weekly KPIs"**
(rapport hebdomadaire de benchmark prix concurrentiel, une page par entreprise cliente)
à l'intérieur de l'app nricher. Tout ce qu'il faut pour que l'intégration soit fidèle au
pixel et que la logique de couleurs/calculs reste cohérente est documenté ici — pas besoin
d'aller chercher ailleurs.

Ce document a été régénéré pour refléter l'état **actuel** (pas une ancienne version) du
site marketing nricher.io, à la date de cette rédaction.

## 1. Contenu de ce dossier

| Fichier | À quoi ça sert |
|---|---|
| `README.md` | ce document — design tokens, logique de calcul, marche à suivre |
| `exemple_rapport.html` | rendu final attendu, avec des données 100% fictives. **Ouvre-le dans un navigateur** (double-clic) : c'est la référence visuelle pixel-perfect — couleurs, espacements, comportements au survol |
| `template_source.html` | le code source (HTML + CSS) qui a généré `exemple_rapport.html`. Sert de référence exacte pour toutes les valeurs CSS concrètes (tailles, couleurs, rayons, espacements, animations). C'est du Jinja2 + CSS vanilla — **pas du code à copier-coller tel quel** dans un composant React/Vue, mais toutes les valeurs y sont, exactes |
| `schema_donnees.json` | le contrat de données : tous les champs nécessaires pour remplir une page, avec des commentaires `_comment` sur les champs qui ont besoin d'explication |

## 2. Design tokens (charte nricher)

```css
/* Couleurs de marque */
--mint:  #60efbe;   /* vert menthe — accent principal */
--blue:  #2e58ca;   /* bleu — accent secondaire, liens, "aligné marché" */

/* Couleurs de statut (Price Index) */
--bad:      #e2452f;                    /* rouge — prix défavorable */
--bad-bg:   rgba(226,69,47,0.10);       /* fond pastel assorti, pour les badges/chips */
--good:     #1fae7a;                    /* vert — prix favorable */
--good-bg:  rgba(31,174,122,0.12);
/* "bleu" (aligné, PI = 100) réutilise --blue avec ce fond : */
--blue-bg:  rgba(46,88,202,0.10);

/* Neutres */
--text:    #1A1D23;
--muted:   #7a8fba;
--border:  rgba(0,0,0,0.08);
--card:    #FFFFFF;

/* Rayons */
--r-md:   14px;
--r-lg:   20px;
--r-pill: 100px;   /* pilules/badges */

/* Typographie */
--font-display: 'Clash Display', 'Syne', sans-serif;   /* titres, chiffres clés */
--font-body:    'Satoshi', 'Inter', -apple-system, sans-serif;   /* texte courant */

/* Easing des animations */
--ease-out: cubic-bezier(.16,1,.3,1);
```

La couleur de marque de l'entreprise cliente (`meta.company_color` dans le JSON, ex:
`#7C3AED`) n'est utilisée qu'à deux endroits : le nom de l'entreprise dans le sommaire
collant, et la 3ᵉ courbe ("3P") du graphique de tendance. Tout le reste de la page suit
la charte nricher ci-dessus, indépendamment du client.

## 3. La règle de couleur — **à appliquer partout, sans exception**

C'est la règle la plus importante de toute la page, et elle doit être **calculée depuis
la valeur**, jamais saisie à la main (voir section 4 pour pourquoi).

> Un Price Index (PI) **< 100** = moins cher que le marché → **vert** (`--good`)
> Un Price Index **= 100** = aligné pile sur le marché → **bleu** (`--blue`)
> Un Price Index **> 100** = plus cher que le marché → **rouge** (`--bad`)

Cette règle s'applique à **tous** les indicateurs PI de la page sans exception : les 3
jauges en haut, le tableau "Price index by article", le classement concurrents, les PI
des tableaux "Competitor/Seller analysis", les barres empilées concurrents/vendeurs/
catégories. Aucun de ces endroits ne doit utiliser une autre logique (ex: pas de palier
orange/jaune intermédiaire, pas de gris neutre à 100 — uniquement ces 3 couleurs).

## 4. Valeurs calculées — ne JAMAIS les laisser saisir à la main

Sur le site marketing, ces valeurs étaient à l'origine des champs libres dans le JSON
d'entrée, remplis à la main par un humain — ça a causé de vraies incohérences (ex: un
indice passant de 104 à 101 affichait "+1%" au lieu de "-3%", parce que le delta avait
été tapé sans recalcul). **Dans l'app, ces 5 valeurs doivent être des champs calculés,
jamais des inputs modifiables par un utilisateur ou pré-remplis par un humain :**

### a) Couleur de sévérité (`severity`)
```js
function piSeverity(value) {
  if (value < 100) return 'good';   // vert
  if (value === 100) return 'blue'; // bleu
  return 'bad';                     // rouge
}
```

### b) Position de l'aiguille des jauges
Jauge semi-circulaire, échelle **90 (gauche) → 120 (droite)**, centre (60,58), rayon 42 :
```js
const GAUGE_CX = 60, GAUGE_CY = 58, GAUGE_R = 42;
const GAUGE_VMIN = 90, GAUGE_VMAX = 120;

function gaugeNeedle(value) {
  const v = Math.max(GAUGE_VMIN, Math.min(GAUGE_VMAX, value)); // clamp
  const frac = (v - GAUGE_VMIN) / (GAUGE_VMAX - GAUGE_VMIN);
  const angleDeg = 180 - frac * 180;
  const angleRad = angleDeg * Math.PI / 180;
  return {
    x: GAUGE_CX + GAUGE_R * Math.cos(angleRad),
    y: GAUGE_CY - GAUGE_R * Math.sin(angleRad),
  };
}
```
L'aiguille est un `<line x1="60" y1="58" x2={needle.x} y2={needle.y} stroke="var(--text)" stroke-width="2.5" stroke-linecap="round"/>` plus un petit `<circle cx="60" cy="58" r="4">` au centre (le pivot).

### c) Remplissage de la barre sous chaque jauge (`bar_pct`)
**Doit utiliser exactement les mêmes bornes (90-120) que l'aiguille ci-dessus**, sinon la
barre et l'aiguille se désynchronisent visuellement (bug réel qu'on a eu) :
```js
function gaugeBarPct(value) {
  const frac = (value - GAUGE_VMIN) / (GAUGE_VMAX - GAUGE_VMIN);
  return Math.round(Math.max(0, Math.min(100, frac * 100))); // clamp 0-100
}
```
Ce même calcul sert aussi pour les barres du classement concurrents (`rank-bar`), avec
`c.pi` à la place de `value` — une seule fonction, réutilisée partout, pour ne jamais
diverger.

### d) Variation vs semaine précédente (`delta_pct`)
Chaque jauge a une valeur `ref_prev` du type `"S24 : 104"` (semaine + valeur). Le delta
affiché (`+1%`, `-3%`...) doit être calculé depuis ces deux nombres, pas tapé à la main :
```js
function gaugeDeltaPct(value, refPrev) {
  const match = /(\d+(?:[.,]\d+)?)\s*$/.exec(String(refPrev));
  if (!match) return null;
  const refValue = parseFloat(match[1].replace(',', '.'));
  if (refValue === 0) return null;
  const pct = (value - refValue) / refValue * 100;
  return (pct >= 0 ? '+' : '') + Math.round(pct) + '%';
}
```

### e) Segments du donut (répartition moyenne lower/equal/higher)
Donut SVG, cercle rayon 50, centré (60,60), qui démarre à midi (rotation -90° sur le
`<g>` parent) :
```js
const DONUT_CX = 60, DONUT_CY = 60, DONUT_R = 50;

function donutSegments(parts /* [{pct, color}, ...] */) {
  const circumference = 2 * Math.PI * DONUT_R;
  let cumulative = 0;
  return parts.map(({ pct, color }) => {
    const length = circumference * (pct / 100);
    const midFraction = circumference ? (cumulative + length / 2) / circumference : 0;
    const angle = midFraction * 2 * Math.PI;
    const xUnrot = DONUT_CX + DONUT_R * Math.cos(angle);
    const yUnrot = DONUT_CY + DONUT_R * Math.sin(angle);
    // applique la meme rotation -90deg que le <g transform> du donut, pour placer
    // correctement le label de % au milieu de chaque arc
    const labelX = DONUT_CX + (yUnrot - DONUT_CY);
    const labelY = DONUT_CY - (xUnrot - DONUT_CX);
    const seg = {
      color, pct,
      dasharray: `${length.toFixed(2)} ${(circumference - length).toFixed(2)}`,
      dashoffset: (-cumulative).toFixed(2),
      labelX: Math.round(labelX * 10) / 10,
      labelY: Math.round(labelY * 10) / 10,
    };
    cumulative += length;
    return seg;
  });
}
```
N'afficher le label `%` que si `pct >= 6` (sinon le texte ne rentre pas dans le segment).

## 5. Anatomie de la page (dans l'ordre)

1. **Nav + sommaire collant** — la vraie nav du site nricher.io (réutilisée telle quelle),
   puis un sommaire (`Price Index / Tendance / Priorité / Vue d'ensemble / Concurrents /
   Vendeurs / Catégories / Conclusion`) qui devient collant sous la nav au scroll, avec le
   nom de l'entreprise affiché à droite (coloré avec `meta.company_color`). **Probablement
   pas pertinent pour l'app** (qui a sa propre nav) — ignorer cette partie côté intégration.
2. **Hero** — titre + accroche (texte rédigé par entreprise, voir section 6), puis 4
   statistiques en cartes (`hero-stats`) : le nombre d'articles analysés/matchés, le PI
   global avec sa flèche ▲/▼, et la date/heure de mise à jour.
3. **Price Index — 3 jauges** — la section la plus importante visuellement. Voir section 4
   pour toute la logique de calcul.
4. **Tendance** — un graphique en courbes (1P/2P/3P, l'indice prix dans le temps) + un
   graphique en barres empilées (répartition moins cher/aligné/plus cher par semaine).
5. **Priorité** — un tableau "Price index by article" filtré par segmentation commerciale
   (Top/Middle/Low sales), avec des badges colorés (même règle de couleur) et des flèches
   de tendance semaine vs semaine précédente.
6. **Vue d'ensemble** — donut (répartition moyenne tous concurrents) + classement à barres
   horizontales (du plus compétitif au plus cher).
7. **Concurrents / Vendeurs / Catégories** — trois sections au même gabarit : une barre
   empilée par ligne (lower/equal/higher %), avec le PI affiché à droite (même règle de
   couleur). "Vendeurs" met en évidence la ligne de l'entreprise cliente elle-même
   (badge "(vous)" + fond légèrement teinté).
8. **Conclusion / Verdict** — un encart de synthèse (texte rédigé) avec 3 chiffres clés.

## 6. Contenu rédigé par entreprise (pas calculable)

Certains champs sont du texte écrit pour chaque rapport hebdomadaire, pas des graphiques :
le titre du hero, la description sous chaque jauge, la note de la table de priorité, et
tout le bloc verdict (tag/titre/texte/3 figures). Sur le site marketing, ces champs
acceptent un format bilingue optionnel `{"fr": "...", "en": "..."}` pour le sélecteur de
langue — **probablement pas utile pour l'app** si elle a son propre système de traduction,
mais à garder en tête si jamais elle doit aussi afficher ce rapport en plusieurs langues.

## 7. Comportements interactifs à reproduire

- Survol des points du graphique de tendance → infobulle avec semaine + valeur (zone de
  survol invisible plus large que le point visible, pour que ce soit facile à déclencher).
- Survol des segments de barres colorées (concurrents/vendeurs/catégories/attractivité) →
  infobulle avec le détail (nom + % exact), le segment s'agrandit légèrement
  (`filter: brightness(1.12); transform: scaleY(1.15)`).
- Survol des jauges Price Index → infobulle avec le delta vs semaine précédente.
- Toutes les cartes (jauges, KPI, barres de classement) se soulèvent légèrement au survol
  (`transform: translateY(-4px à -6px)` + ombre portée qui s'intensifie).

## 8. Format des données

Voir `schema_donnees.json` pour le contrat complet, commenté. Points clés :
- `meta.source_label` est obligatoire : doit toujours indiquer honnêtement la provenance
  de la donnée affichée (donnée publique scrapée vs donnée client sous contrat).
- Les champs `needle_x`/`needle_y`/`bar_pct`/`severity`/`delta_pct` des jauges **ne
  doivent pas être dans le JSON d'entrée** — ils sont entièrement calculés (section 4).
  Si l'app stocke ces données en base, ne stocker que `value`/`label`/`ref_prev`/`desc` ;
  recalculer le reste à l'affichage à chaque fois (comme ça, si la formule change un
  jour, tous les rapports — anciens et nouveaux — en bénéficient automatiquement).

## 9. Marche à suivre pour l'intégration

1. Ouvrir `exemple_rapport.html` dans un navigateur, à côté de l'écran où tu codes — c'est
   la référence visuelle de vérité à chaque étape.
2. Repérer dans `template_source.html` la section du composant que tu intègres (les
   sections sont commentées et dans le même ordre que la section 5 ci-dessus), et reporter
   les valeurs CSS exactes (tailles, couleurs, espacements) dans tes composants.
3. Pour tout ce qui est **calculé** (jauges, couleurs, deltas, donut) : ne pas copier de
   valeurs en dur depuis l'exemple — réimplémenter les fonctions de la section 4 dans le
   langage de l'app, et les brancher sur les vraies données.
4. Vérifier au fur et à mesure avec des données limites : un PI exactement à 100 (doit
   être bleu), un PI à 99 et à 101 (vert / rouge), une jauge à 90 et à 120 (bords de
   l'échelle, aiguille à plat à gauche/droite).
5. Si un doute persiste sur une valeur précise (rayon, marge, couleur), elle est forcément
   dans `template_source.html` — chercher la classe CSS correspondante plutôt que d'
   estimer au pixel depuis le rendu.
