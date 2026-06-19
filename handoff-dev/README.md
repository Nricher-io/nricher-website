# Page "Weekly KPIs" — à intégrer dans l'app

Contexte : ceci est la maquette d'une page de rapport hebdomadaire (benchmark prix
concurrentiel) qu'on veut proposer dans l'app nricher, une page par entreprise cliente.

## Ce qu'il y a dans ce dossier

- **`exemple_rapport.html`** → ouvre ce fichier directement dans un navigateur (double-clic).
  C'est le rendu final attendu, avec des données fictives. C'est la référence visuelle
  pixel-perfect : couleurs, espacements, comportements au survol (tooltips, hover sur
  les graphiques et les barres).

- **`schema_donnees.json`** → le contrat de données. Décrit tous les champs nécessaires
  pour remplir une page, avec un commentaire `_comment` à côté des champs qui ont besoin
  d'explication. C'est ce qui doit driver la requête API / le modèle de données côté app.

- **`template_source.html`** → le code source (HTML + CSS) qui a généré `exemple_rapport.html`.
  Sert de référence exacte pour les valeurs CSS (tailles, couleurs, rayons, espacements)
  si besoin de les répliquer dans un composant React/Vue/autre. Ce n'est pas du code à
  copier-coller tel quel (c'est du Jinja2 + CSS vanilla), mais toutes les valeurs concrètes
  y sont.

## Design tokens (charte nricher)

```
--mint:  #60efbe   (vert)
--blue:  #2e58ca   (bleu)
--bad:   #e2452f   (rouge, prix défavorable)
--good:  #1fae7a   (vert, prix favorable)
--warn:  #ffc14d   (orange, attention)

Police titres : Clash Display (700)
Police texte  : Satoshi (400/500/700/900)
Chargées via Fontshare : https://api.fontshare.com
```

## Comportements interactifs à reproduire

- Survol des points du graphique de tendance → infobulle avec semaine + valeur
- Survol des segments de barres colorées (concurrents/vendeurs/catégories) → infobulle
  avec le détail, le segment s'agrandit légèrement
- Survol des jauges Price Index → infobulle avec le delta vs semaine précédente
- Les cartes (jauges, KPI) se soulèvent légèrement au survol (transform + ombre)

## Logique de couleur (à respecter)

Un indice prix (PI) > 100 = plus cher que le marché → rouge/orange (mauvais).
Un indice prix < 100 = moins cher que le marché → vert (bon).
= 100 = aligné → neutre/gris.
Cette règle s'applique partout : jauges, tableau "Price index by article", chips PI.

## Champ obligatoire — ne pas oublier

`meta.source_label` doit toujours indiquer honnêtement la provenance de la donnée
affichée (donnée publique scrapée vs donnée client sous contrat). Ce n'est pas affiché
visuellement dans la version actuelle de la maquette mais c'est une règle de fond à
garder en tête côté produit.
