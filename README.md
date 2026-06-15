# nricher — Site marketing

Site marketing statique de **nricher**, plateforme de product data intelligence pour retailers et e-commerçants.

## Structure

```
site/
├── index.html              # Page d'accueil
├── le-bon-catalogue.html   # Page produit — Le bon produit (gestion catalogue)
├── le-bon-prix.html        # Page produit — Le bon prix (benchmark pricing)
├── bien-presente.html      # Page produit — Bien présenté (enrichissement fiches)
├── l-outil.html            # Page technologie — Comment fonctionne nricher
├── cas-clients.html        # Page cas clients — Études de cas avec modales
├── lequipe.html            # Page équipe + valeurs + recrutement
├── contact.html            # Page contact + formulaire démo
├── merci.html              # Page de confirmation après soumission formulaire
├── css/
│   └── main.css            # Feuille de style principale (~1 300 lignes)
├── js/
│   ├── main.js             # Scripts principaux (~600 lignes)
│   └── zoom-persist.js     # Persistance du niveau de zoom navigateur
└── img/                    # Assets visuels
    ├── le bon prix/        # Captures d'écran interface Le bon prix
    ├── le bon produit/     # Captures d'écran interface Le bon produit
    ├── bien présenté/      # Captures d'écran interface Bien présenté
    ├── screenshots/        # Éléments graphiques transverses (filet, etc.)
    ├── logos/              # Logos partenaires / clients
    ├── nricher logo/       # Logo nricher (SVG)
    ├── photos/             # Photos équipe
    └── récompenses/        # Visuels trophées et distinctions
```

## Stack technique

- HTML / CSS / JavaScript vanilla — aucune dépendance, aucun framework
- Police **Satoshi** (variable font, chargée via CDN Fontshare)
- Design system basé sur des custom properties CSS (`--blue`, `--mint`, `--card`, etc.)

## Fonctionnalités notables

- **Animations reveal** au scroll (`IntersectionObserver`)
- **Split text hero** — titre découpé lettre par lettre à l'entrée
- **Orbite prix** — 7 captures produit qui tournent autour du logo prix central (le-bon-prix)
- **Colonnes défilantes** — images produit en scroll infini (index, bien-présenté)
- **Marquee** — défilement horizontal d'images produit (index)
- **Diagramme cycle** — SVG interactif Le bon produit / Bien présenté / Le bon prix, rotation automatique toutes les 10 s
- **Questions animées** — 3 questions qui se succèdent avec barres de progression cliquables
- **Tabs interfaces** — navigation par onglets pour les captures d'interface (feats-showcase)
- **Modales cas clients** — détail des études de cas en overlay
- **Formulaire contact** — Formspree (sans backend)
- **Curseur personnalisé** — dot + ring animé
- **Parallax** — léger effet de profondeur sur le hero et les sections glow
- **Grain** — texture noise CSS en overlay sur toute la page

## Identité visuelle

| Variable | Valeur | Usage |
|---|---|---|
| `--blue` | `#3D5AFF` | Couleur principale |
| `--mint` | `#2EFFA8` | Couleur accent nricher |
| `--text` | `#0A0C14` | Texte principal |
| `--muted` | `#6B7280` | Texte secondaire |
| `--card` | `#FFFFFF` | Fond des cartes |
| `--mid` | `#F8F9FB` | Fond sections alternées |

Le dégradé signature `linear-gradient(to right, var(--blue), var(--mint))` est appliqué sur les mots-clés mis en avant (`grad-text`).
