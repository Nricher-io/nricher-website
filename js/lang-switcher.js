(function () {
  'use strict';

  var lang = localStorage.getItem('nr-lang') || 'fr';
  var translations = window.NRICHER_TRANSLATIONS || {};
  var originalTexts = {};

  function initTranslation() {
    // 1. Scan and store original French values for all data-i18n elements
    var elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      if (!originalTexts[key]) {
        originalTexts[key] = {
          html: el.innerHTML,
          content: el.getAttribute('content') || null,
          placeholder: el.getAttribute('placeholder') || null,
          alt: el.getAttribute('alt') || null,
          title: el.getAttribute('title') || null,
          ariaLabel: el.getAttribute('aria-label') || null
        };
      }
    });

    // 2. Apply saved/default language
    applyLanguage(lang);

    // 3. Setup click listeners (toggle dropdown + pick an option), event delegation
    document.addEventListener('click', function (e) {
      var toggleBtn = e.target.closest('.lang-switch__btn');
      if (toggleBtn) {
        var wrap = toggleBtn.closest('.lang-switch');
        var wasOpen = wrap.classList.contains('is-open');
        document.querySelectorAll('.lang-switch.is-open').forEach(function (w) { w.classList.remove('is-open'); });
        if (!wasOpen) {
          wrap.classList.add('is-open');
          toggleBtn.setAttribute('aria-expanded', 'true');
        } else {
          toggleBtn.setAttribute('aria-expanded', 'false');
        }
        return;
      }

      var option = e.target.closest('.lang-switch__option');
      if (option) {
        applyLanguage(option.getAttribute('data-lang'));
        document.querySelectorAll('.lang-switch.is-open').forEach(function (w) {
          w.classList.remove('is-open');
          var btn = w.querySelector('.lang-switch__btn');
          if (btn) btn.setAttribute('aria-expanded', 'false');
        });
        return;
      }

      // Click outside any lang-switch: close all open menus
      if (!e.target.closest('.lang-switch')) {
        document.querySelectorAll('.lang-switch.is-open').forEach(function (w) {
          w.classList.remove('is-open');
          var btn = w.querySelector('.lang-switch__btn');
          if (btn) btn.setAttribute('aria-expanded', 'false');
        });
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        document.querySelectorAll('.lang-switch.is-open').forEach(function (w) { w.classList.remove('is-open'); });
      }
    });
  }

  function applyLanguage(l) {
    lang = l;
    localStorage.setItem('nr-lang', l);
    document.documentElement.setAttribute('lang', l);

    var transDict = translations[l] || {};
    var elements = document.querySelectorAll('[data-i18n]');

    elements.forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      var orig = originalTexts[key] || {};

      if (l === 'fr') {
        // Restore original French
        if (el.tagName === 'META') {
          if (orig.content) el.setAttribute('content', orig.content);
        } else if (el.tagName === 'TITLE') {
          document.title = orig.html;
          el.innerHTML = orig.html;
        } else if (el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') {
          el.innerHTML = orig.html;
        }
        if (orig.placeholder) el.setAttribute('placeholder', orig.placeholder);
        if (orig.alt) el.setAttribute('alt', orig.alt);
        if (orig.title) el.setAttribute('title', orig.title);
        if (orig.ariaLabel) el.setAttribute('aria-label', orig.ariaLabel);
      } else {
        // Translate to English/other
        // A. Inner HTML/Text / Meta / Title
        var htmlTrans = transDict[key];
        if (htmlTrans !== undefined) {
          if (el.tagName === 'META') {
            el.setAttribute('content', htmlTrans);
          } else if (el.tagName === 'TITLE') {
            document.title = htmlTrans;
            el.innerHTML = htmlTrans;
          } else if (el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') {
            el.innerHTML = htmlTrans;
          }
        }

        // B. Attributes
        var placeholderTrans = transDict[key + '.placeholder'];
        if (placeholderTrans !== undefined) el.setAttribute('placeholder', placeholderTrans);

        var altTrans = transDict[key + '.alt'];
        if (altTrans !== undefined) el.setAttribute('alt', altTrans);

        var titleTrans = transDict[key + '.title'];
        if (titleTrans !== undefined) el.setAttribute('title', titleTrans);

        var ariaTrans = transDict[key + '.aria-label'];
        if (ariaTrans !== undefined) el.setAttribute('aria-label', ariaTrans);
      }
    });

    // 4. Update the active class of switcher options across the DOM
    document.querySelectorAll('.lang-switch').forEach(function (wrap) {
      wrap.querySelectorAll('.lang-switch__option').forEach(function (opt) {
        opt.classList.toggle('is-active', opt.getAttribute('data-lang') === l);
      });
    });

    // 5. Update body labels or attributes if used by page analytics
    var labelTrans = transDict['body.data-screen-label'];
    if (labelTrans) {
      document.body.setAttribute('data-screen-label', labelTrans);
    } else {
      var origLabel = document.body.getAttribute('data-screen-label');
      if (origLabel && l === 'fr') {
        // Simple recovery if needed
      }
    }
  }

  // Run as soon as DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTranslation);
  } else {
    initTranslation();
  }

  // Expose switcher globally
  window.nrApplyLanguage = applyLanguage;
})();
