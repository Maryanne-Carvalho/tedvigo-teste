/* Ted Vigo — site behaviour (no dependencies). */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduceMotion = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;

  /* ------------------------------------------------------------------
     Header: solid on scroll, mobile menu, current-section highlight
  ------------------------------------------------------------------ */
  var header = $('#site-header');
  var nav = $('#main-nav');
  var toggle = $('#menu-toggle');
  function onScroll() { header.classList.toggle('is-solid', window.scrollY > 40); }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  function setMenu(open, returnFocus) {
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
    header.classList.toggle('menu-open', open);
    document.body.classList.toggle('no-scroll', open);
    if (open) { var first = $('a', nav); if (first) first.focus(); }
    else if (returnFocus) toggle.focus();
  }
  toggle.addEventListener('click', function () { setMenu(toggle.getAttribute('aria-expanded') !== 'true'); });
  $$('a', nav).forEach(function (a) { a.addEventListener('click', function () { if (nav.classList.contains('is-open')) setMenu(false); }); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) setMenu(false, true);
  });
  document.addEventListener('click', function (e) {
    if (nav.classList.contains('is-open') && !header.contains(e.target)) setMenu(false);
  });
  matchMedia('(min-width: 1181px)').addEventListener('change', function (m) { if (m.matches) setMenu(false); });

  // highlight the section in view
  if ('IntersectionObserver' in window) {
    var links = {};
    $$('a[href^="#"]', nav).forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var watched = ['home', 'books', 'cup', 'peoples-cup', 'audiobooks', 'trailers', 'film', 'about'];
    var visible = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { visible[en.target.id] = en.isIntersecting; });
      var current = null;
      // last watched element (document order) that is in the band
      watched.forEach(function (id) { if (visible[id]) current = id; });
      Object.keys(links).forEach(function (id) {
        if (id === current) links[id].setAttribute('aria-current', 'true');
        else links[id].removeAttribute('aria-current');
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    watched.forEach(function (id) { var el = document.getElementById(id); if (el) io.observe(el); });
  }

  /* ------------------------------------------------------------------
     Book carousels
  ------------------------------------------------------------------ */
  $$('.book-group').forEach(function (group) {
    var track = $('.car-track', group), prev = $('.prev', group), next = $('.next', group);
    var bar = $('.car-progress span', group);
    if (!track) return;
    function update() {
      var max = track.scrollWidth - track.clientWidth;
      var isStatic = max <= 4;
      group.classList.toggle('is-static', isStatic);
      $('.carousel', group).classList.toggle('is-static', isStatic);
      prev.disabled = track.scrollLeft <= 4;
      next.disabled = track.scrollLeft >= max - 4;
      var w = Math.min(100, track.clientWidth / track.scrollWidth * 100);
      bar.style.setProperty('--w', w + '%');
      bar.style.setProperty('--x', (max > 0 ? track.scrollLeft / max * (100 - w) : 0) + '%');
    }
    function step(dir) {
      var card = $('.book-card', track);
      var gap = parseFloat(getComputedStyle(track).columnGap) || 24;
      var per = Math.max(1, Math.floor((track.clientWidth + gap) / (card.offsetWidth + gap)));
      track.scrollBy({ left: dir * per * (card.offsetWidth + gap), behavior: reduceMotion ? 'auto' : 'smooth' });
    }
    prev.addEventListener('click', function () { step(-1); });
    next.addEventListener('click', function () { step(1); });
    track.addEventListener('scroll', update, { passive: true });
    track.addEventListener('keydown', function (e) {
      if (e.target !== track) return;
      if (e.key === 'ArrowRight') { step(1); e.preventDefault(); }
      if (e.key === 'ArrowLeft') { step(-1); e.preventDefault(); }
    });
    addEventListener('resize', update);
    addEventListener('load', update);
    update();
  });

  /* ------------------------------------------------------------------
     Dialog helpers (synopsis + video)
  ------------------------------------------------------------------ */
  var supportsDialog = typeof HTMLDialogElement === 'function' && 'showModal' in document.createElement('dialog');
  var lastOpener = null;
  function openDialog(d, opener) {
    lastOpener = opener || document.activeElement;
    d.showModal();
    document.body.classList.add('no-scroll');
  }
  $$('dialog.modal').forEach(function (d) {
    $$('[data-close]', d).forEach(function (b) { b.addEventListener('click', function () { d.close(); }); });
    d.addEventListener('click', function (e) { if (e.target === d) d.close(); });   // backdrop click
    d.addEventListener('close', function () {
      document.body.classList.remove('no-scroll');
      if (lastOpener && document.contains(lastOpener)) lastOpener.focus();
    });
  });

  /* Synopsis: the <details> keeps working without JS; with JS it opens a reading dialog. */
  var syn = $('#synopsis-modal');
  if (supportsDialog) {
    $$('.book-card').forEach(function (card) {
      var summary = $('.synopsis-details summary', card);
      summary.setAttribute('aria-haspopup', 'dialog');
      summary.addEventListener('click', function (e) {
        e.preventDefault();
        var frame = $('.cover-frame', card).cloneNode(true);
        var img = $('img', frame); img.removeAttribute('loading'); img.removeAttribute('onerror'); img.hidden = false;
        var coverBox = $('.syn-cover', syn); coverBox.innerHTML = ''; coverBox.appendChild(frame);
        $('.syn-cat', syn).innerHTML = $('.book-category', card).innerHTML;
        $('.syn-title', syn).innerHTML = $('.book-title', card).innerHTML;
        var body = $('.syn-body', syn); body.innerHTML = '';
        var p = document.createElement('p'); p.innerHTML = $('.book-synopsis', card).innerHTML; body.appendChild(p);
        var ex = $('.syn-explore', syn), src = $('.book-access', card);
        ex.href = src.getAttribute('href'); ex.innerHTML = src.innerHTML;
        openDialog(syn, summary);
        $('.modal-shell', syn).scrollTop = 0;
        $('.modal-close', syn).focus();
      });
    });
    $('.syn-explore', syn).addEventListener('click', function () { syn.close(); });
  }

  /* Video player: one dialog, video loaded only on demand, no autoplay without a click. */
  var vdlg = $('#video-modal'), video = $('video', vdlg);
  $$('.play-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var title = $('h3', btn.closest('.video-card')).textContent;
      if (!supportsDialog) { window.open(btn.dataset.video, '_blank'); return; }
      video.poster = btn.dataset.poster;
      video.src = btn.dataset.video;
      video.setAttribute('aria-label', title);
      $('.vid-title', vdlg).textContent = title;
      openDialog(vdlg, btn);
      var pr = video.play(); if (pr && pr.catch) pr.catch(function () {});
    });
  });
  vdlg.addEventListener('close', function () { video.pause(); video.removeAttribute('src'); video.load(); });

  /* ------------------------------------------------------------------
     Captain Quin interactive teaser — original srcdoc loaded lazily
  ------------------------------------------------------------------ */
  var teaser = $('#teaser-frame'), teaserRequested = false, currentLang = 'en';
  function teaserDoc(lang) {
    var doc = window.TEASER_SRCDOC;
    var tr = lang !== 'en' && window.I18N && window.I18N[lang] && window.I18N[lang]._teaser;
    if (!tr) return doc;   // English: byte-identical original
    doc = doc.replace('<html lang="pt-BR">', '<html lang="' + (window.I18N[lang]._htmlLang || lang) + '">');
    Object.keys(tr).forEach(function (en) {
      var t = tr[en];
      doc = doc.split('>' + en + '<').join('>' + t + '<').split("'" + en + "'").join("'" + t + "'");
    });
    return doc;
  }
  function renderTeaser() { if (window.TEASER_SRCDOC) teaser.srcdoc = teaserDoc(currentLang); }
  function loadTeaser() {
    if (teaserRequested) return; teaserRequested = true;
    var s = document.createElement('script'); s.src = 'assets/js/teaser-srcdoc.js'; s.onload = renderTeaser;
    document.body.appendChild(s);
  }
  if ('IntersectionObserver' in window) {
    var tio = new IntersectionObserver(function (en) { if (en[0].isIntersecting) { loadTeaser(); tio.disconnect(); } }, { rootMargin: '600px 0px' });
    tio.observe(teaser);
  } else loadTeaser();

  /* ------------------------------------------------------------------
     Languages. English = the text already in the page (never overwritten).
     A language is offered only if its dictionary covers every key.
  ------------------------------------------------------------------ */
  var LANGS = [
    { code: 'en', name: 'English', short: 'EN' },
    { code: 'pt', name: 'Português', short: 'PT' },
    { code: 'es', name: 'Español', short: 'ES' }
  ];
  var ATTRS = [['alt', 'alt'], ['aria', 'aria-label'], ['title', 'title'], ['content', 'content'], ['roledesc', 'aria-roledescription']];
  var D = window.I18N || {};
  var nodes = [], keys = {};
  $$('[data-i18n]').forEach(function (el) { var k = el.getAttribute('data-i18n'); keys[k] = 1; nodes.push({ el: el, k: k, attr: null, en: el.innerHTML }); });
  ATTRS.forEach(function (pair) {
    $$('[data-i18n-' + pair[0] + ']').forEach(function (el) {
      var k = el.getAttribute('data-i18n-' + pair[0]); keys[k] = 1;
      nodes.push({ el: el, k: k, attr: pair[1], en: el.getAttribute(pair[1]) });
    });
  });
  var allKeys = Object.keys(keys);
  function complete(code) {
    if (code === 'en') return true;
    var d = D[code]; if (!d) return false;
    var missing = allKeys.filter(function (k) { return typeof d[k] !== 'string' || !d[k].trim(); });
    if (missing.length && window.console) console.warn('[i18n] "' + code + '" hidden, missing keys:', missing);
    return !missing.length;
  }
  var available = LANGS.filter(function (l) { return complete(l.code); });

  var langBtn = $('#lang-btn'), langMenu = $('#lang-menu');
  function applyLang(code, save) {
    var d = D[code];
    nodes.forEach(function (n) {
      var v = code === 'en' ? n.en : d[n.k];
      if (n.attr) n.el.setAttribute(n.attr, v); else if (n.el.innerHTML !== v) n.el.innerHTML = v;
    });
    root.lang = code === 'en' ? 'en' : (d._htmlLang || code);
    var L = LANGS.filter(function (l) { return l.code === code; })[0];
    $('.flag use', langBtn).setAttribute('href', '#flag-' + code);
    $('.lang-name', langBtn).textContent = L.name;
    $('.lang-code', langBtn).textContent = L.short;
    $$('button', langMenu).forEach(function (b) { b.setAttribute('aria-checked', String(b.dataset.lang === code)); });
    if (code !== currentLang) { currentLang = code; if (teaserRequested) renderTeaser(); }
    if (save) { try { localStorage.setItem('tv-lang', code); } catch (e) {} }
    window.dispatchEvent(new Event('resize'));   // carousels re-measure
  }
  function closeLangMenu(focusBtn) {
    langMenu.hidden = true; langBtn.setAttribute('aria-expanded', 'false');
    if (focusBtn) langBtn.focus();
  }
  function openLangMenu(focusIndex) {
    langMenu.hidden = false; langBtn.setAttribute('aria-expanded', 'true');
    var items = $$('button', langMenu);
    var i = typeof focusIndex === 'number' ? focusIndex : Math.max(0, items.findIndex(function (b) { return b.getAttribute('aria-checked') === 'true'; }));
    items[(i + items.length) % items.length].focus();
  }

  if (available.length > 1) {
    available.forEach(function (l) {
      var li = document.createElement('li'); li.setAttribute('role', 'none');
      var b = document.createElement('button');
      b.type = 'button'; b.setAttribute('role', 'menuitemradio'); b.dataset.lang = l.code; b.lang = l.code;
      b.innerHTML = '<svg class="flag" aria-hidden="true"><use href="#flag-' + l.code + '"/></svg><span class="lm-name">' + l.name +
        '</span><span class="lm-code" aria-hidden="true">' + l.short + '</span><svg class="lm-check" aria-hidden="true"><use href="#i-check"/></svg>';
      b.addEventListener('click', function () { applyLang(l.code, true); closeLangMenu(true); });
      li.appendChild(b); langMenu.appendChild(li);
    });
    langBtn.addEventListener('click', function () { langMenu.hidden ? openLangMenu() : closeLangMenu(); });
    langBtn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); openLangMenu(0); }
      if (e.key === 'ArrowUp') { e.preventDefault(); openLangMenu(-1); }
    });
    langMenu.addEventListener('keydown', function (e) {
      var items = $$('button', langMenu), i = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
      else if (e.key === 'Home') { e.preventDefault(); items[0].focus(); }
      else if (e.key === 'End') { e.preventDefault(); items[items.length - 1].focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); closeLangMenu(true); }
      else if (e.key === 'Tab') closeLangMenu();
    });
    document.addEventListener('click', function (e) { if (!langMenu.hidden && !$('#lang').contains(e.target)) closeLangMenu(); });

    var saved = null;
    try { saved = localStorage.getItem('tv-lang'); } catch (e) {}
    var q = (location.search.match(/[?&]lang=(\w+)/) || [])[1];
    var start = [q, saved].filter(function (c) { return c && available.some(function (l) { return l.code === c; }); })[0] || 'en';
    applyLang(start, !!q);
  } else {
    $('#lang').hidden = true;
  }
  root.classList.remove('i18n-pending');
})();
