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
      brands: ['ambientedirect', 'Andlight', 'batinea', 'Bestmobilier', 'Bifor', 'chiaracolombini', 'connox', 'design-bestseller', 'drawer', 'fermliving', 'finnishdesignshop', 'flos', 'Galerieslafayette', 'gautier', 'grouperg', 'Inside_75', 'Jardindeco', 'Lacompagniedulit', 'lamptwist', 'lecedrerouge', 'light11', 'Lightonline', 'Madeindesign', 'madeindesign de', 'madeindesignuk', 'Maisons du Monde', 'maisons du monde es', 'maisons du monde it', 'Manelli', 'maxibazar', 'mabeoindustries', 'myareadesign', 'Nedgis', 'Neuvieme_store', 'Nouveau marchand', 'onelec', 'Passions Cadeaux', 'red deco', 'Silvera', 'Unamourdetapis', 'Vente Unique', 'vente unique de', 'vente unique es', 'vente unique it', 'Weber', 'westwing', 'Manor', 'Printemps', '3Suisses']
    },
    {
      id: 'bricolage-jardin',
      name: 'Bricolage & Jardin',
      brands: ['Bricomarche', 'Castorama', 'leroy merlin', 'leroy merlin es', 'leroy merlin it', 'Manomano', 'manomano es', 'manomano it', 'Hydrozone']
    },
    {
      id: 'sport-outdoor',
      name: 'Sport & Outdoor',
      brands: ['alltricks', 'alpiniste', 'ekosport', 'glisshop', 'hardloop', 'Icasque', 'irun', 'skapetze', 'Snowleader', 'Snowleader CH', 'sportdecouverte', 'trekkinn', 'centrale du casque']
    },
    {
      id: 'beaute-parfumerie',
      name: 'Beauté & Parfumerie',
      brands: ['aurlane', 'Boticinal', 'Clarins', 'Cocooncenter', 'Easyparapharmacie', 'Lancome', 'LOreal', 'Payot', 'Pharmazon', 'sephora', 'Sisley', 'SVR', 'Atida']
    },
    {
      id: 'mode-luxe',
      name: 'Mode & Luxe',
      brands: ['bulgari', 'Hermes', 'JPG', 'Sandro', 'Sandro_BDV', 'SenNoSen', 'debenhams']
    },
    {
      id: 'electronique-hightech',
      name: 'Électronique & High-Tech',
      brands: ['Boulanger', 'BUT', 'Darty', 'Fnac', 'Pixmania', 'Ubaldi', 'bq', 'CDiscount', 'Rue du commerce']
    },
    {
      id: 'mobilite',
      name: 'Mobilité (Auto, Moto, Vélo)',
      brands: ['Dafymoto', 'Louis Moto', 'Motoaxxe', 'Motoblouz', 'Motocard', 'Teamaxe', 'Voltex', 'WTB', 'speedway', 'Mobin']
    },
    {
      id: 'bebe-puericulture',
      name: 'Bébé & Puériculture',
      brands: ['berceaumagique', 'madeinbebe', 'Petit Bateau', 'vertbaudet']
    },
    {
      id: 'grande-distribution',
      name: 'Grande distribution & Généraliste',
      brands: ['auchan', 'Carrefour', 'carrefour es', 'Conforama', 'conforama es', 'Amazon', 'amazon es', 'amazon it', 'Rakuten', 'shopping_feed']
    },
    {
      id: 'culture-loisirs',
      name: 'Culture & Loisirs',
      brands: ['cultura', 'viapresse', 'Belong', 'Bewak', 'Labecanerie', 'Maxxess', 'Thecoolrepublic', 'Underdog', 'zoomici', 'Asteri', 'Simplybearings']
    }
  ];
})();
