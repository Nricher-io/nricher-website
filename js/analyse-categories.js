// Mapping categorie -> entreprises scrapees, utilise par les pages
// analyse-pricing.html / analyse-quality.html / analyse-catalogue.html
// pour la recherche/selection de categorie. Categories construites a la main
// a partir des 137 marques suivies par nricher (data/companies.json) -
// approximatif par endroits, a affiner si besoin.
// "packs" = sous-categories produit (ex: Climatiseur, Salon de jardin...)
// comparees entre les memes enseignes au sein d'une categorie - utilise par
// le mode swipe de la fiche d'analyse Catalogue. Inventes a la main, a
// affiner une fois la vraie taxonomie produit connectee.
(function () {
  'use strict';

  window.NRICHER_CATEGORIES = [
    {
      id: 'maison-deco',
      name: 'Maison & Décoration',
      brands: ['Maisons du Monde', 'Madeindesign', 'Vente Unique', 'Nedgis', 'Silvera', 'Jardindeco', 'gautier', 'light11', 'connox', 'maxibazar'],
      packs: ['Luminaire & Éclairage', 'Tapis & Textile', 'Mobilier salon & salle à manger']
    },
    {
      id: 'bricolage-jardin',
      name: 'Bricolage & Jardin',
      brands: ['Castorama', 'leroy merlin', 'Manomano', 'manomano it'],
      packs: ['Climatiseur & Ventilateur', 'Salon de jardin', 'Barbecue']
    },
    {
      id: 'sport-outdoor',
      name: 'Sport & Outdoor',
      brands: ['alltricks', 'alpiniste', 'ekosport', 'glisshop', 'hardloop', 'irun', 'Snowleader', 'Snowleader CH', 'trekkinn'],
      packs: ['Vélo & Cyclisme', 'Ski & Snowboard', 'Trail & Running']
    },
    {
      id: 'beaute-parfumerie',
      name: 'Beauté & Parfumerie',
      brands: ['aurlane', 'sephora'],
      packs: ['Parfumerie', 'Soin du visage']
    },
    {
      id: 'electronique-hightech',
      name: 'Électronique & High-Tech',
      brands: ['Boulanger', 'BUT', 'Darty', 'Fnac', 'bq'],
      packs: ['Téléviseurs', 'Smartphones', 'Petit électroménager']
    },
    {
      id: 'grande-distribution',
      name: 'Hypermarchés & Grande distribution',
      brands: ['auchan', 'Carrefour', 'carrefour es', 'Conforama', 'conforama es'],
      packs: ['Épicerie', 'Textile & Mode', 'Électroménager']
    },
    {
      id: 'marketplaces',
      name: 'Marketplaces en ligne',
      brands: ['Amazon', 'amazon es', 'amazon it', 'CDiscount', 'Rue du commerce'],
      packs: ['Informatique', 'Mode', 'Maison & Jardin']
    },
    {
      id: 'culture-loisirs',
      name: 'Culture & Loisirs',
      brands: ['Thecoolrepublic', 'Underdog', 'Asteri', 'Simplybearings'],
      packs: ['Jeux & Jouets', 'Librairie', 'Presse & Magazines']
    }
  ];
})();
