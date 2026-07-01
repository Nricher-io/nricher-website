// Charge les catégories de marché depuis le JSON statique généré par
// nricher-engine/generate_market_analysis.py.
// Emet 'nricherCategoriesReady' sur document quand les données sont prêtes.
(function () {
  'use strict';

  fetch('/data/market-analysis/categories.json')
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function (data) {
      window.NRICHER_CATEGORIES = data;
      document.dispatchEvent(new CustomEvent('nricherCategoriesReady'));
    })
    .catch(function (err) {
      console.warn('[nricher] categories.json:', err);
      window.NRICHER_CATEGORIES = [];
      document.dispatchEvent(new CustomEvent('nricherCategoriesReady'));
    });
})();
