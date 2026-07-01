(function () {
  'use strict';

  var lang = localStorage.getItem('nr-lang') || 'fr';
  var translations = window.NRICHER_TRANSLATIONS || {};
  var originalTexts = {};
  var originalTips = [];

  // Weekly KPIs report pages inject their own per-company English text (hero,
  // gauge descriptions, verdict...) — merge it into the common English dictionary
  // so the same data-i18n mechanism picks it up like everything else on the site.
  if (window.NRICHER_REPORT_I18N) {
    translations.en = translations.en || {};
    for (var reportKey in window.NRICHER_REPORT_I18N) {
      translations.en[reportKey] = window.NRICHER_REPORT_I18N[reportKey];
    }
  }

  // Hover-tooltip (data-tip) text mixes static French words with dynamic values
  // (names, weeks, percentages) baked in server-side — translate just the known words.
  var TIP_WORDS = [
    ['Moins cher', 'Cheaper'],
    ['Aligné', 'Aligned'],
    ['Plus cher', 'More expensive'],
    ['moins cher', 'cheaper'],
    ['aligné', 'aligned'],
    ['plus cher', 'more expensive']
  ];
  function translateTip(text) {
    TIP_WORDS.forEach(function (pair) { text = text.split(pair[0]).join(pair[1]); });
    return text;
  }

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

    // 1b. Scan and store original French values for all hover-tooltip (data-tip) elements
    document.querySelectorAll('[data-tip]').forEach(function (el) {
      originalTips.push({ el: el, fr: el.getAttribute('data-tip') });
    });

    // 2. Apply saved/default language
    applyLanguage(lang);

    // Reveal the page now that translation (if any) is applied — avoids a flash of
    // untranslated French content on pages loaded with English already selected.
    document.documentElement.style.visibility = '';

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

    // 3b. Translate hover-tooltip (data-tip) text
    // data-tip-en attribute takes priority over the generic word-by-word translateTip()
    originalTips.forEach(function (t) {
      var enTip = t.el.getAttribute('data-tip-en');
      t.el.setAttribute('data-tip', l === 'fr' ? t.fr : (enTip || translateTip(t.fr)));
    });

    // 3c. Weekly KPIs report pages: reformat the "mis a jour le" timestamp from its
    // raw ISO value client-side, instead of relying on the French string baked
    // server-side (Python) which never changes language. No-op on other pages.
    document.querySelectorAll('[data-generated-at]').forEach(function (el) {
      var iso = el.getAttribute('data-generated-at');
      if (!iso) return;
      var date = new Date(iso);
      if (isNaN(date.getTime())) return;
      el.textContent = new Intl.DateTimeFormat(l === 'fr' ? 'fr-FR' : 'en-US', {
        day: 'numeric', month: 'long', hour: 'numeric', minute: '2-digit'
      }).format(date);
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
