/* ============================================================
   nricher — main.js v2
   Lenis · GSAP + ScrollTrigger · Cursor · Split text · Reveals
   ============================================================ */
(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = window.matchMedia('(pointer:fine)').matches;

  /* ----------------------------------------------------------------
     0. Wait for DOM + scripts
  ---------------------------------------------------------------- */
  function init() {

    /* ----------------------------------------------------------------
       1. Lenis smooth scroll (désactivé — lag molette Windows)
    ---------------------------------------------------------------- */
    var lenis;
    /* Lenis désactivé : scroll natif, animations GSAP inchangées */

    /* ----------------------------------------------------------------
       2. Scroll progress bar
    ---------------------------------------------------------------- */
    var progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
      if (reduce) {
        gsap.set(progressBar, { scaleX: 1 });
      } else {
        gsap.to(progressBar, {
          scaleX: 1, ease: 'none',
          scrollTrigger: { trigger: document.body, start: 'top top', end: 'bottom bottom', scrub: 0 }
        });
      }
    }

    /* ----------------------------------------------------------------
       3. Sticky nav
    ---------------------------------------------------------------- */
    var nav = document.querySelector('.nav');
    function checkNav() {
      if (!nav) return;
      nav.classList.toggle('is-scrolled', window.scrollY > 28);
    }
    window.addEventListener('scroll', checkNav, { passive: true });
    checkNav();

    /* ----------------------------------------------------------------
       4. Mobile menu
    ---------------------------------------------------------------- */
    var burger   = document.querySelector('.nav__burger');
    var backdrop = document.querySelector('.menu-backdrop');
    function closeMenu() { document.body.classList.remove('menu-open'); }
    if (burger)   burger.addEventListener('click', function () { document.body.classList.toggle('menu-open'); });
    if (backdrop) backdrop.addEventListener('click', closeMenu);
    document.querySelectorAll('.mobile-menu__close').forEach(function (btn) { btn.addEventListener('click', closeMenu); });
    document.querySelectorAll('.mobile-menu a').forEach(function (a) { a.addEventListener('click', closeMenu); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });

    /* Highlight current page in mobile menu */
    (function () {
      var page = window.location.pathname.split('/').pop() || 'index.html';
      if (page === '') page = 'index.html';
      document.querySelectorAll('.mobile-menu a:not(.btn)').forEach(function (a) {
        if (a.getAttribute('href') === page) a.classList.add('is-current');
      });
    })();

    /* Barre de recherche hero -> autocomplete live + acces direct au rapport */
    (function () {
      var form = document.getElementById('hero-search-form');
      var input = document.getElementById('hero-search-input');
      var dropdown = document.getElementById('hero-search-dropdown');
      if (!form || !input || !dropdown) return;

      var companies = window.NRICHER_COMPANIES || [];
      var MAX_RESULTS = 6;

      function closeDropdown() { dropdown.classList.remove('is-open'); dropdown.innerHTML = ''; }

      function renderDropdown(query) {
        var q = query.trim().toLowerCase();
        if (!q) { closeDropdown(); return; }

        var matches = companies.filter(function (c) { return c.name.toLowerCase().indexOf(q) !== -1; });

        if (matches.length === 0) {
          dropdown.innerHTML = '<div class="hero__search-dropdown__empty">Aucune entreprise trouvée</div>';
          dropdown.classList.add('is-open');
          return;
        }

        var html = matches.slice(0, MAX_RESULTS).map(function (c) {
          var badge = c.available
            ? '<span class="hero__search-dropdown__badge hero__search-dropdown__badge--ok">Voir le rapport</span>'
            : '<span class="hero__search-dropdown__badge hero__search-dropdown__badge--no">Bientôt</span>';
          var disabledClass = c.available ? '' : ' is-disabled';
          return '<div class="hero__search-dropdown__item' + disabledClass + '" data-slug="' + c.slug + '" data-available="' + c.available + '">' +
                 '<span>' + c.name + '</span>' + badge + '</div>';
        }).join('');

        if (matches.length > MAX_RESULTS) {
          html += '<div class="hero__search-dropdown__more" data-seeall="1">Voir les ' + matches.length + ' résultats →</div>';
        }

        dropdown.innerHTML = html;
        dropdown.classList.add('is-open');
      }

      input.addEventListener('input', function () { renderDropdown(input.value); });
      input.addEventListener('focus', function () { if (input.value.trim()) renderDropdown(input.value); });

      dropdown.addEventListener('click', function (e) {
        var item = e.target.closest('.hero__search-dropdown__item');
        if (item) {
          if (item.dataset.available === 'true') {
            window.location.href = 'rapports/' + item.dataset.slug + '.html';
          }
          return;
        }
        if (e.target.closest('[data-seeall]')) {
          window.location.href = 'recherche.html?q=' + encodeURIComponent(input.value.trim());
        }
      });

      document.addEventListener('click', function (e) {
        if (!form.contains(e.target) && !dropdown.contains(e.target)) closeDropdown();
      });

      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var q = input.value.trim();
        window.location.href = 'recherche.html' + (q ? '?q=' + encodeURIComponent(q) : '');
      });
    })();

    /* ----------------------------------------------------------------
       5. Custom cursor (fine-pointer only)
    ---------------------------------------------------------------- */
    if (finePointer && !reduce) {
      var dot  = document.querySelector('.cur-dot');
      var ring = document.querySelector('.cur-ring');
      if (dot && ring) {
        var dotX  = gsap.quickTo(dot,  'x', { duration: 0.12, ease: 'power3.out' });
        var dotY  = gsap.quickTo(dot,  'y', { duration: 0.12, ease: 'power3.out' });
        var ringX = gsap.quickTo(ring, 'x', { duration: 0.45, ease: 'power3.out' });
        var ringY = gsap.quickTo(ring, 'y', { duration: 0.45, ease: 'power3.out' });

        window.addEventListener('mousemove', function (e) {
          dotX(e.clientX); dotY(e.clientY);
          ringX(e.clientX); ringY(e.clientY);
        });

        var hoverEls = document.querySelectorAll('a, button, [data-cursor-hover]');
        hoverEls.forEach(function (el) {
          el.addEventListener('mouseenter', function () { ring.classList.add('is-hover'); });
          el.addEventListener('mouseleave', function () { ring.classList.remove('is-hover'); });
        });

        document.addEventListener('mouseleave', function () {
          gsap.to([dot, ring], { opacity: 0, duration: 0.2 });
        });
        document.addEventListener('mouseenter', function () {
          gsap.to([dot, ring], { opacity: 1, duration: 0.2 });
        });
      }
    }

    /* ----------------------------------------------------------------
       6. Split-text entrance (hero) — line-based
    ---------------------------------------------------------------- */
    if (!reduce) {
      var splitEls = document.querySelectorAll('[data-split-hero]');
      splitEls.forEach(function (el) {
        var inners = el.querySelectorAll('.split-inner');
        if (!inners.length) return;
        gsap.set(inners, { yPercent: 115 });
        gsap.to(inners, {
          yPercent: 0,
          duration: 1.1,
          stagger: 0.06,
          ease: 'expo.out',
          delay: 0.15,
        });
      });

      /* data-split-scroll: same but triggered on scroll */
      var scrollSplits = document.querySelectorAll('[data-split-scroll]');
      scrollSplits.forEach(function (el) {
        var inners = el.querySelectorAll('.split-inner');
        if (!inners.length) return;
        gsap.set(inners, { yPercent: 115 });
        ScrollTrigger.create({
          trigger: el, start: 'top 85%',
          onEnter: function () {
            gsap.to(inners, { yPercent: 0, duration: 1.0, stagger: 0.06, ease: 'expo.out' });
          }, once: true
        });
      });
    }

    /* ----------------------------------------------------------------
       7. Reveal animations (IntersectionObserver — robust)
    ---------------------------------------------------------------- */
    var reveals  = Array.prototype.slice.call(document.querySelectorAll('.reveal'));

    function inView(el) {
      var r = el.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      return r.top < vh * 0.88 && r.bottom > 0;
    }

    if (reduce) {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    } else if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -8% 0px' });
      reveals.forEach(function (el) {
        if (inView(el)) el.classList.add('is-in');
        else io.observe(el);
      });
    } else {
      /* fallback: scroll + rect */
      function checkReveals() {
        for (var i = reveals.length - 1; i >= 0; i--) {
          if (inView(reveals[i])) { reveals[i].classList.add('is-in'); reveals.splice(i, 1); }
        }
      }
      window.addEventListener('scroll', checkReveals, { passive: true });
      checkReveals();
      setTimeout(checkReveals, 200);
    }

    /* ----------------------------------------------------------------
       8. Animated counters
    ---------------------------------------------------------------- */
    function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }
    function animateCount(el) {
      if (el.__counted) return; el.__counted = true;
      var target   = parseFloat(el.getAttribute('data-count'));
      var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
      var prefix   = el.getAttribute('data-prefix') || '';
      var suffix   = el.getAttribute('data-suffix') || '';
      if (reduce) { el.textContent = prefix + target.toFixed(decimals).replace('.', ',') + suffix; return; }
      var dur = 1500, start = null;
      function frame(ts) {
        if (!start) start = ts;
        var p = Math.min((ts - start) / dur, 1);
        el.textContent = prefix + (target * easeOutCubic(p)).toFixed(decimals).replace('.', ',') + suffix;
        if (p < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }
    var counters = Array.prototype.slice.call(document.querySelectorAll('[data-count]'));
    if ('IntersectionObserver' in window) {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) { animateCount(e.target); cio.unobserve(e.target); } });
      }, { threshold: 0.5 });
      counters.forEach(function (el) {
        if (el.getBoundingClientRect().top < window.innerHeight * 0.9) animateCount(el);
        else cio.observe(el);
      });
    } else { counters.forEach(animateCount); }

    /* ----------------------------------------------------------------
       9. Dashboard bar fill
    ---------------------------------------------------------------- */
    function fillBars() {
      document.querySelectorAll('[data-bar]').forEach(function (bar) {
        var h = bar.getAttribute('data-bar');
        if (reduce) { bar.style.height = h; return; }
        setTimeout(function () { bar.style.height = h; }, 200 + Math.random() * 500);
      });
    }
    setTimeout(fillBars, 300);

    /* ----------------------------------------------------------------
       10. Marquee velocity-skew (Lenis onScroll)
    ---------------------------------------------------------------- */
    if (window.gsap && !reduce) {
      var marquees = document.querySelectorAll('.marquee-inner');
      if (marquees.length && lenis) {
        var skew = 0;
        var skewSetter = gsap.quickSetter('.marquee-inner', 'skewX', 'deg');
        var clamp = gsap.utils.clamp(-7, 7);
        lenis.on('scroll', function (e) {
          var vel = e.velocity || 0;
          skew = clamp(vel * 0.008);
          skewSetter(skew);
        });
      }
    }

    /* ----------------------------------------------------------------
       11. Scrolling image-columns parallax (hero, index only)
    ---------------------------------------------------------------- */
    if (window.gsap && !reduce) {
      var col1 = document.querySelector('.hero__col--1');
      var col2 = document.querySelector('.hero__col--2');
      if (col1 && col2) {
        gsap.to(col1, { yPercent: -12, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
        gsap.to(col2, { yPercent:  20, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
      }
    }

    /* ----------------------------------------------------------------
       12. Cursor parallax glow (mousemove lerp)
    ---------------------------------------------------------------- */
    if (finePointer && !reduce) {
      document.querySelectorAll('[data-parallax]').forEach(function (scene) {
        var glows = scene.querySelectorAll('[data-glow]');
        if (!glows.length) return;
        var tx = 0, ty = 0, cx = 0, cy = 0, raf = null;
        scene.addEventListener('mousemove', function (e) {
          var r = scene.getBoundingClientRect();
          tx = ((e.clientX - r.left) / r.width  - 0.5) * 2;
          ty = ((e.clientY - r.top)  / r.height - 0.5) * 2;
          if (!raf) raf = requestAnimationFrame(loop);
        });
        scene.addEventListener('mouseleave', function () { tx = 0; ty = 0; });
        function loop() {
          cx += (tx - cx) * 0.06; cy += (ty - cy) * 0.06;
          glows.forEach(function (g, i) {
            var d = (i + 1) * 18;
            g.style.transform = 'translate(' + (cx * d) + 'px,' + (cy * d) + 'px)';
          });
          if (Math.abs(tx - cx) > 0.001 || Math.abs(ty - cy) > 0.001) raf = requestAnimationFrame(loop);
          else raf = null;
        }
      });
    }

    /* ----------------------------------------------------------------
       13. Clients logo rotation
    ---------------------------------------------------------------- */
    var ALL_CLIENTS = [
      { name: 'Boulanger',            url: 'img/logos/boulanger.png',              wide: true  },
      { name: 'BUT',                  url: 'img/logos/but.png',                    wide: false },
      { name: 'Carrefour',            url: 'img/logos/carrefour.svg',              wide: true  },
      { name: 'Castorama',            url: 'img/logos/castorama.png',              wide: true  },
      { name: 'Conforama',            url: 'img/logos/conforama.png',              wide: true  },
      { name: 'Fnac',                 url: 'img/logos/fnac.png',                   wide: false },
      { name: 'La Redoute',           url: 'img/logos/la-redoute.png',             wide: false },
      { name: "L'Oréal",              url: "img/logos/L'Oréal.svg",               wide: true  },
      { name: 'Nedgis',               url: 'img/logos/nedgis.png',                 wide: true  },
      { name: 'Rakuten',              url: 'img/logos/rakuten.png',                wide: true  },
      { name: 'Vente-Unique',         url: 'img/logos/vente-unique.webp',          wide: true  },
      { name: 'Made in Design',       url: 'img/logos/made in design.svg',         wide: true  },
      { name: 'Berceau Magique',      url: 'img/logos/Berceau magique.png',        wide: true,  filter: 'invert(1) grayscale(100%) opacity(0.30)' },
      { name: 'Darty',                url: 'img/logos/darty.png',                  wide: true  },
      { name: 'Gauthier',             url: 'img/logos/gauthier.png',               wide: false },
      { name: 'Groupe RG',            url: 'img/logos/groupe RG.png',              wide: false },
      { name: 'La Compagnie du Lit',  url: 'img/logos/la compagnie du lit.png',    wide: true  },
      { name: 'Sport Découverte',     url: 'img/logos/sport découverte.svg',       wide: true  },
      { name: 'Underlog',             url: 'img/logos/underlog.png',               wide: false },
      { name: 'Viapresse',            url: 'img/logos/viapresse.png',              wide: false },
    ];

    var strip  = document.getElementById('clients-strip') || document.getElementById('clients-grid');
    var strip2 = document.getElementById('clients-strip-2');
    if (strip) {
      var slots1 = Array.prototype.slice.call(strip.querySelectorAll('.clients__logo'));
      var slots2 = strip2 ? Array.prototype.slice.call(strip2.querySelectorAll('.clients__logo')) : [];
      var slots = slots1.concat(slots2);
      var totalSlots = slots.length;

      var shuffled = ALL_CLIENTS.slice().sort(function () { return Math.random() - 0.5; });
      var shown = shuffled.slice(0, totalSlots);

      function renderSlot(slot, client) {
        slot.innerHTML = '';
        var img = document.createElement('img');
        img.alt = client.name;
        img.src = client.url;
        if (client.filter) img.style.filter = client.filter;
        img.onerror = (function (c, s) {
          return function () {
            s.innerHTML = '';
            var txt = document.createElement('span');
            txt.textContent = c.name;
            s.appendChild(txt);
          };
        })(client, slot);
        slot.appendChild(img);
      }

      slots.forEach(function (slot, i) { if (shown[i]) renderSlot(slot, shown[i]); });

      setInterval(function () {
        var shownNames = shown.map(function (c) { return c ? c.name : ''; });
        var available = ALL_CLIENTS.filter(function (c) { return shownNames.indexOf(c.name) === -1; });
        var swapCount = Math.min(5, available.length);
        if (swapCount === 0) return;

        var allIdx = [];
        for (var ii = 0; ii < totalSlots; ii++) allIdx.push(ii);
        var indices = allIdx.sort(function () { return Math.random() - 0.5; }).slice(0, swapCount);
        var picks   = available.sort(function () { return Math.random() - 0.5; }).slice(0, swapCount);

        indices.forEach(function (slotIdx, i) {
          if (!picks[i]) return;
          var slot = slots[slotIdx];
          var newClient = picks[i];
          slot.classList.add('is-swapping');
          setTimeout((function (s, c, idx) {
            return function () {
              shown[idx] = c;
              renderSlot(s, c);
              s.classList.remove('is-swapping');
            };
          })(slot, newClient, slotIdx), 350);
        });
      }, 2500);
    }

    /* ----------------------------------------------------------------
       14. Feature showcase — rAF-driven progress (true pause/resume)
    ---------------------------------------------------------------- */
    var showcase = document.querySelector('.feats-showcase');
    if (showcase) {
      var fTabs    = Array.prototype.slice.call(showcase.querySelectorAll('.feat-tab'));
      var fSlides  = Array.prototype.slice.call(showcase.querySelectorAll('.feat-slide'));
      var fCurrent = 0;
      var fPaused  = false;
      var fElapsed = 0;
      var fLastTs  = null;
      var fRaf     = null;
      var F_DUR    = 6000;

      /* Dot indicators (mobile) */
      var fDots = [];
      var fDotsWrap = document.createElement('div');
      fDotsWrap.className = 'feats-dots';
      fSlides.forEach(function (_, i) {
        var d = document.createElement('button');
        d.className = 'feats-dot';
        d.setAttribute('aria-label', 'Slide ' + (i + 1));
        d.addEventListener('click', function () { fActivate(i); if (!fPaused) fRun(); });
        fDotsWrap.appendChild(d);
        fDots.push(d);
      });
      var fPanel = showcase.querySelector('.feats-panel');
      if (fPanel) fPanel.after(fDotsWrap); else showcase.appendChild(fDotsWrap);

      function fBar(idx) { return fTabs[idx] && fTabs[idx].querySelector('.feat-tab__progress'); }

      function fSetBar(idx, pct) {
        var b = fBar(idx);
        if (b) { b.style.transition = 'none'; b.style.width = pct + '%'; }
      }

      function fActivate(idx) {
        if (fTabs[fCurrent]) fTabs[fCurrent].classList.remove('is-active');
        fSlides[fCurrent].classList.remove('is-active');
        if (fDots[fCurrent]) fDots[fCurrent].classList.remove('is-active');
        fSetBar(fCurrent, 0);
        fCurrent = idx;
        if (fTabs[fCurrent]) fTabs[fCurrent].classList.add('is-active');
        fSlides[fCurrent].classList.add('is-active');
        if (fDots[fCurrent]) fDots[fCurrent].classList.add('is-active');
        fElapsed = 0;
        fLastTs  = null;
      }

      function fTick(ts) {
        if (fPaused) { fRaf = null; return; }
        if (fLastTs !== null) fElapsed += ts - fLastTs;
        fLastTs = ts;
        if (fElapsed >= F_DUR) {
          fSetBar(fCurrent, 100);
          fActivate((fCurrent + 1) % fTabs.length);
          fRaf = requestAnimationFrame(fTick);
          return;
        }
        fSetBar(fCurrent, (fElapsed / F_DUR) * 100);
        fRaf = requestAnimationFrame(fTick);
      }

      function fRun() {
        if (fRaf) cancelAnimationFrame(fRaf);
        fRaf = requestAnimationFrame(fTick);
      }

      fTabs.forEach(function (tab, i) {
        tab.addEventListener('click', function () {
          fActivate(i);
          if (!fPaused) fRun();
        });
      });

      showcase.addEventListener('mouseenter', function () {
        fPaused = true;
        fLastTs = null;
      });
      showcase.addEventListener('mouseleave', function () {
        fPaused = false;
        fRun();
      });

      /* Swipe tactile sur mobile */
      var fTouchX = null;
      showcase.addEventListener('touchstart', function (e) {
        fTouchX = e.touches[0].clientX;
        fPaused = true; fLastTs = null;
      }, { passive: true });
      showcase.addEventListener('touchend', function (e) {
        if (fTouchX === null) return;
        var dx = e.changedTouches[0].clientX - fTouchX;
        fTouchX = null;
        if (Math.abs(dx) < 30) { fPaused = false; fRun(); return; }
        var next = dx < 0
          ? (fCurrent + 1) % fSlides.length
          : (fCurrent - 1 + fSlides.length) % fSlides.length;
        fActivate(next);
        fPaused = false; fRun();
      }, { passive: true });

      document.addEventListener('visibilitychange', function () {
        if (document.hidden) { fPaused = true; fLastTs = null; }
        else if (showcase) { fPaused = false; fRun(); }
      });

      fActivate(0);
      fRun();
    }

    /* ----------------------------------------------------------------
       15. Modals — cas clients
    ---------------------------------------------------------------- */
    function openModal(id) {
      var m = document.getElementById(id);
      if (!m) return;
      m.classList.add('is-open');
      document.body.classList.add('modal-open');
      var close = m.querySelector('.modal__close');
      if (close) setTimeout(function () { close.focus(); }, 50);
    }
    function closeModal(m) {
      if (!m) return;
      m.classList.remove('is-open');
      document.body.classList.remove('modal-open');
    }

    document.querySelectorAll('[data-modal]').forEach(function (btn) {
      btn.addEventListener('click', function () { openModal(btn.getAttribute('data-modal')); });
    });
    document.querySelectorAll('.modal__close').forEach(function (btn) {
      btn.addEventListener('click', function () { closeModal(btn.closest('.modal')); });
    });
    document.querySelectorAll('.modal__overlay').forEach(function (ov) {
      ov.addEventListener('click', function () { closeModal(ov.closest('.modal')); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        var open = document.querySelector('.modal.is-open');
        if (open) closeModal(open);
      }
    });

    /* ----------------------------------------------------------------
       16. Trophy card 3D tilt
    ---------------------------------------------------------------- */
    if (finePointer && !reduce) {
      document.querySelectorAll('.trophy-card').forEach(function (card) {
        var shine  = card.querySelector('.trophy-card__shine');
        var rotStr = card.style.getPropertyValue('--rot') || '0deg';
        var baseRot = parseFloat(rotStr) || 0;
        var raf = null;
        var mx = 0, my = 0;

        card.addEventListener('mousemove', function (e) {
          var r = card.getBoundingClientRect();
          mx = (e.clientX - r.left) / r.width  - 0.5;
          my = (e.clientY - r.top)  / r.height - 0.5;
          if (!raf) raf = requestAnimationFrame(drawTilt);
        });

        card.addEventListener('mouseleave', function () {
          mx = 0; my = 0;
          card.style.transform = 'rotate(' + baseRot + 'deg)';
          if (shine) shine.style.background = '';
          raf = null;
        });

        function drawTilt() {
          card.style.transform =
            'perspective(640px) rotate(0deg) scale(1.07)' +
            ' rotateY(' + (mx * 20) + 'deg)' +
            ' rotateX(' + (-my * 16) + 'deg)';
          if (shine) {
            shine.style.background =
              'radial-gradient(circle at ' + ((mx + 0.5) * 100) + '% ' +
              ((my + 0.5) * 100) + '%, rgba(255,255,255,0.55), transparent 60%)';
          }
          raf = null;
        }
      });
    }

    /* ----------------------------------------------------------------
       17. Questions animées
    ---------------------------------------------------------------- */
    (function () {
      var qList = document.getElementById('qs-list');
      if (!qList) return;
      var qItems = Array.prototype.slice.call(qList.querySelectorAll('.qs-item'));
      var qDots  = Array.prototype.slice.call(document.querySelectorAll('#qs-prog .qs-dot'));
      var qCur = 0;
      var qTimer = null;
      function qActivate(idx) {
        qItems[qCur].classList.remove('is-active');
        if (qDots[qCur]) qDots[qCur].classList.remove('is-active');
        qCur = idx;
        qItems[qCur].classList.add('is-active');
        if (qDots[qCur]) qDots[qCur].classList.add('is-active');
      }
      function qStartAuto() {
        clearInterval(qTimer);
        if (reduce) return;
        qTimer = setInterval(function () {
          qActivate((qCur + 1) % qItems.length);
        }, 3200);
      }
      qDots.forEach(function (dot, i) {
        dot.style.cursor = 'pointer';
        dot.addEventListener('click', function () { qActivate(i); qStartAuto(); });
      });
      qStartAuto();
    })();

    /* ----------------------------------------------------------------
       18. Cycle diagram — clic sur nœud ou label
    ---------------------------------------------------------------- */
    (function () {
      var ring = document.getElementById('cycle-ring');
      if (!ring) return;
      var nodes  = Array.prototype.slice.call(ring.querySelectorAll('.cycle-node'));
      var labels = Array.prototype.slice.call(ring.querySelectorAll('.cycle-lbl'));
      var outers = Array.prototype.slice.call(ring.querySelectorAll('.cycle-node-outer'));

      function activate(idx) {
        nodes.forEach(function (n)  { n.classList.remove('is-active'); });
        labels.forEach(function (l) { l.classList.remove('is-active'); });
        outers.forEach(function (o) { o.classList.remove('is-tooltip-open'); });
        if (nodes[idx])  nodes[idx].classList.add('is-active');
        if (labels[idx]) labels[idx].classList.add('is-active');
        if (outers[idx]) outers[idx].classList.add('is-tooltip-open');
      }

      var current = 0;
      var timer = null;

      function startAuto() {
        clearInterval(timer);
        timer = setInterval(function () {
          current = (current + 1) % nodes.length;
          activate(current);
        }, 5000);
      }

      nodes.forEach(function (node, i) {
        node.addEventListener('click', function () {
          current = i;
          activate(i);
          startAuto();
        });
      });
      labels.forEach(function (lbl) {
        lbl.style.cursor = 'pointer';
        lbl.addEventListener('click', function () {
          current = parseInt(lbl.getAttribute('data-idx'), 10);
          activate(current);
          startAuto();
        });
      });

      /* Hover : affiche uniquement le tooltip du nœud survolé */
      outers.forEach(function (outer, i) {
        outer.addEventListener('mouseenter', function () {
          clearInterval(timer);
          activate(i);
          current = i;
        });
        outer.addEventListener('mouseleave', function () {
          startAuto();
        });
      });

      /* Stoppe la rotation quand la souris est sur un tooltip */
      var tooltips = Array.prototype.slice.call(ring.querySelectorAll('.cycle-tooltip'));
      tooltips.forEach(function (tip) {
        tip.addEventListener('mouseenter', function () {
          clearInterval(timer);
        });
        tip.addEventListener('mouseleave', function () {
          startAuto();
        });
      });

      activate(0);
      startAuto();
    })();

    /* ----------------------------------------------------------------
       19. Glows globaux — drift continu + parallax molette
    ---------------------------------------------------------------- */
    (function () {
      var glowA = document.createElement('div');
      glowA.className = 'bg-glow bg-glow--a';
      var glowB = document.createElement('div');
      glowB.className = 'bg-glow bg-glow--b';
      document.body.prepend(glowB);
      document.body.prepend(glowA);

      if (reduce) return; /* statiques pour reduced-motion */

      var t0 = performance.now();
      function tick() {
        var t  = (performance.now() - t0) / 1000;
        var sy = window.scrollY;
        /* oscillation lente + offset molette */
        var ax = Math.sin(t * 0.22) * 55;
        var ay = Math.cos(t * 0.17) * 72 + sy * 0.07;
        var bx = Math.cos(t * 0.19) * 65;
        var by = Math.sin(t * 0.14) * 84 - sy * 0.05;
        glowA.style.transform = 'translate(' + ax + 'px,' + ay + 'px)';
        glowB.style.transform = 'translate(' + bx + 'px,' + by + 'px)';
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    })();

    /* ----------------------------------------------------------------
       20. Upload CV — affichage du nom de fichier sélectionné
    ---------------------------------------------------------------- */
    (function () {
      document.querySelectorAll('.recruit-form__upload input[type="file"]').forEach(function (fileInput) {
        fileInput.addEventListener('change', function () {
          var wrap = fileInput.closest('.recruit-form__upload');
          var txt  = wrap ? wrap.querySelector('.recruit-form__upload-text') : null;
          var ico  = wrap ? wrap.querySelector('.recruit-form__upload-icon') : null;
          if (!txt) return;
          if (fileInput.files && fileInput.files.length > 0) {
            var f  = fileInput.files[0];
            var kb = Math.round(f.size / 1024);
            var size = kb > 1024 ? (Math.round(kb / 102.4) / 10) + ' Mo' : kb + ' Ko';
            txt.innerHTML = '<strong>' + f.name + '</strong><br><span style="opacity:.6">' + size + ' · prêt à envoyer</span>';
            if (ico) ico.textContent = '✅';
            wrap.style.borderColor  = 'var(--mint)';
            wrap.style.borderStyle  = 'solid';
            wrap.style.background   = 'rgba(96,239,190,0.06)';
          } else {
            txt.innerHTML = '<strong>Cliquer pour joindre</strong> ou glisser-déposer votre CV';
            if (ico) ico.textContent = '📎';
            wrap.style.borderColor = '';
            wrap.style.borderStyle = '';
            wrap.style.background  = '';
          }
        });
      });
    })();

    /* ----------------------------------------------------------------
       21. Soumission AJAX des formulaires → redirect vers merci.html
           (les fichiers sont retirés du FormData : Formspree plan
            gratuit ne supporte pas les pièces jointes — le CV est
            transmis séparément par email de confirmation)
    ---------------------------------------------------------------- */
    (function () {
      var forms = document.querySelectorAll('form[data-ajax]');
      forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
          e.preventDefault();
          var redirect = form.getAttribute('data-redirect') || 'merci.html';
          var btn      = form.querySelector('[type="submit"]');
          var btnText  = btn ? btn.innerHTML : '';
          if (btn) { btn.disabled = true; btn.innerHTML = 'Envoi en cours…'; }

          var data = new FormData(form);
          /* retire les fichiers — évite le rejet 422 de Formspree free plan */
          form.querySelectorAll('input[type="file"]').forEach(function (fi) {
            data.delete(fi.name);
          });

          fetch(form.action, {
            method: 'POST',
            body: data,
            headers: { 'Accept': 'application/json' }
          }).then(function (r) {
            if (r.ok) {
              window.location.href = redirect;
            } else {
              if (btn) { btn.disabled = false; btn.innerHTML = btnText; }
              alert('Une erreur est survenue. Merci de réessayer.');
            }
          }).catch(function () {
            if (btn) { btn.disabled = false; btn.innerHTML = btnText; }
            alert('Connexion impossible. Vérifiez votre réseau et réessayez.');
          });
        });
      });
    })();

    /* ----------------------------------------------------------------
       grad-text — premier mot en bleu, reste en vert mint
    ---------------------------------------------------------------- */
    (function () {
      var els = Array.prototype.slice.call(document.querySelectorAll('.grad-text'));
      els.forEach(function (el) {
        var text = el.textContent;
        var spaceIdx = text.indexOf(' ');
        if (spaceIdx === -1) return; /* mot unique → reste mint via CSS */
        var first = text.slice(0, spaceIdx);
        var rest  = text.slice(spaceIdx);
        el.innerHTML =
          '<span style="-webkit-text-fill-color:#2e58ca;color:#2e58ca;">' + first + '</span>' +
          '<span style="-webkit-text-fill-color:#60efbe;color:#60efbe;">' + rest + '</span>';
      });
    })();

  } /* end init() */

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

})();
