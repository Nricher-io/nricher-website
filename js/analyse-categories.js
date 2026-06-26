// Mapping categorie -> entreprises scrapees, utilise par les pages
// analyse-pricing.html / analyse-quality.html / analyse-catalogue.html
// pour la recherche/selection de categorie. Categories construites a la main
// a partir des 137 marques suivies par nricher (data/companies.json) -
// approximatif par endroits, a affiner si besoin.
(function () {
  'use strict';

  window.NRICHER_CATEGORIES = [
    {
      id: 'maison-deco',
      name: 'Maison & Décoration',
      brands: ['Andlight', 'chiaracolombini', 'connox', 'design-bestseller', 'drawer', 'fermliving', 'gautier', 'grouperg', 'Jardindeco', 'lamptwist', 'lecedrerouge', 'light11', 'Madeindesign', 'madeindesign de', 'madeindesignuk', 'Maisons du Monde', 'maisons du monde es', 'maisons du monde it', 'maxibazar', 'myareadesign', 'Nedgis', 'Silvera', 'Vente Unique', 'vente unique de', 'vente unique es', 'vente unique it']
    },
    {
      id: 'bricolage-jardin',
      name: 'Bricolage & Jardin',
      brands: ['Castorama', 'leroy merlin', 'Manomano', 'manomano it']
    },
    {
      id: 'sport-outdoor',
      name: 'Sport & Outdoor',
      brands: ['alltricks', 'alpiniste', 'ekosport', 'glisshop', 'hardloop', 'irun', 'Snowleader', 'Snowleader CH', 'trekkinn']
    },
    {
      id: 'beaute-parfumerie',
      name: 'Beauté & Parfumerie',
      brands: ['aurlane', 'sephora']
    },
    {
      id: 'electronique-hightech',
      name: 'Électronique & High-Tech',
      brands: ['Boulanger', 'BUT', 'Darty', 'Fnac', 'bq']
    },
    {
      id: 'grande-distribution',
      name: 'Hypermarchés & Grande distribution',
      brands: ['auchan', 'Carrefour', 'carrefour es', 'Conforama', 'conforama es']
    },
    {
      id: 'marketplaces',
      name: 'Marketplaces en ligne',
      brands: ['Amazon', 'amazon es', 'amazon it', 'CDiscount', 'Rue du commerce']
    },
    {
      id: 'culture-loisirs',
      name: 'Culture & Loisirs',
      brands: ['Thecoolrepublic', 'Underdog', 'Asteri', 'Simplybearings']
    }
  ];
})();
