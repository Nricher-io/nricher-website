/* Reset — supprime tout zoom CSS résiduel et nettoie le localStorage */
(function () {
  try { localStorage.removeItem('nricher_dpr'); } catch (e) {}
  document.documentElement.style.zoom = '';
})();
