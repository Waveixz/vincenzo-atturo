/* app.js — VA Digital (safe + include-ready, sticky mobile always) */

(() => {
  "use strict";

  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ===========================
     Menu tondo
     =========================== */
  function initMenu() {
    const BREAKPOINT = 900;
    const btn  = $(".menu-toggle");
    const menu = $("#menu");
    if (!btn || !menu) return;

    if (btn.dataset.inited === "1") return;
    btn.dataset.inited = "1";

    const links = $$("a[href]", menu);
    const mqlMobile = window.matchMedia(`(max-width: ${BREAKPOINT}px)`);

    let keydownBound = null;
    let clickOutsideBound = null;

    function isOpen(){ return menu.classList.contains("open"); }

    function closeMenu({ restoreFocus = true } = {}) {
      if (!isOpen()) return;
      menu.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
      if (restoreFocus) btn.focus();

      if (keydownBound) document.removeEventListener("keydown", keydownBound, true);
      if (clickOutsideBound) document.removeEventListener("click", clickOutsideBound, true);
      keydownBound = null;
      clickOutsideBound = null;
    }

    function onKeydown(e) {
      if (e.key === "Escape") { e.preventDefault(); closeMenu(); return; }
      if (!isOpen() || !mqlMobile.matches || links.length === 0) return;

      if (e.key === "Tab") {
        const first = links[0];
        const last  = links[links.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    }

    function onClickOutside(e) {
      if (!isOpen()) return;
      const inside = menu.contains(e.target) || btn.contains(e.target);
      if (!inside) closeMenu({ restoreFocus: false });
    }

    function openMenu() {
      if (isOpen()) return;
      menu.classList.add("open");
      btn.setAttribute("aria-expanded", "true");
      if (links.length) links[0].focus();

      keydownBound = onKeydown;
      clickOutsideBound = onClickOutside;
      document.addEventListener("keydown", keydownBound, true);
      document.addEventListener("click", clickOutsideBound, true);
    }

    function toggleMenu(){ isOpen() ? closeMenu() : openMenu(); }

    links.forEach(a => a.addEventListener("click", () => {
      if (mqlMobile.matches) closeMenu({ restoreFocus: false });
    }));

    mqlMobile.addEventListener("change", () => {
      if (!mqlMobile.matches) closeMenu({ restoreFocus: false });
    });

    btn.addEventListener("click", toggleMenu);

    closeMenu({ restoreFocus: false });
  }

  /* ===========================
     Dropdown (GENERICA)
     =========================== */
  function initDropdowns() {
    const dropdowns = $$("[data-dd]");
    if (dropdowns.length === 0) return;

    dropdowns.forEach(dd => {
      if (dd.dataset.inited === "1") return;
      dd.dataset.inited = "1";

      const btn = $(".va-dd__btn", dd);
      const list = $(".va-dd__list", dd);
      const valueEl = $("[data-dd-value]", dd);
      const hidden = $('input[type="hidden"]', dd);
      const items = $$(".va-dd__item", dd);

      if (!btn || !list || !valueEl || !hidden || items.length === 0) return;

      function open(){
        dd.classList.add("is-open");
        btn.setAttribute("aria-expanded","true");
        list.setAttribute("tabindex","-1");
        list.focus();
      }
      function close(){
        dd.classList.remove("is-open");
        btn.setAttribute("aria-expanded","false");
      }
      function setValue(v){
        valueEl.textContent = v;
        hidden.value = v;
        items.forEach(it => it.classList.toggle("is-selected", it.dataset.value === v));
        close();
      }

      btn.addEventListener("click", (e) => {
        e.preventDefault();
        dd.classList.contains("is-open") ? close() : open();
      });

      items.forEach(it => {
        it.addEventListener("click", (e) => {
          e.preventDefault();
          setValue(it.dataset.value);
        });
        it.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setValue(it.dataset.value);
          }
        });
      });

      document.addEventListener("click", (e) => { if (!dd.contains(e.target)) close(); }, true);
      document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); }, true);
    });

    /* ===========================
       CTA pacchetti -> precompila dropdown pacchetto (solo se esiste)
       =========================== */
    $$("[data-package]").forEach(btn => {
      if (btn.dataset.inited === "1") return;
      btn.dataset.inited = "1";

      btn.addEventListener("click", () => {
        const pkg = btn.getAttribute("data-package")?.trim();
        if (!pkg) return;

        const dd = document.querySelector('[data-dd] input[name="pacchetto"]')?.closest("[data-dd]");
        if (!dd) return;

        const hidden = $('input[type="hidden"]', dd);
        const valueEl = $("[data-dd-value]", dd);

        if (hidden) hidden.value = pkg;
        if (valueEl) valueEl.textContent = pkg;

        dd.querySelectorAll(".va-dd__item").forEach(it => {
          it.classList.toggle("is-selected", it.dataset.value === pkg);
        });
      });
    });
  }

  /* ===========================
     Form contatto (mailto)
     =========================== */
  function initContactForm() {
    const form = $("#contact-form");
    if (!form) return;
    if (form.dataset.inited === "1") return;
    form.dataset.inited = "1";

    form.addEventListener("submit", function(e){
      e.preventDefault();

      const nome = form.querySelector('[name="nome"]')?.value || '';
      const email = form.querySelector('[name="email"]')?.value || '';
      const servizio = form.querySelector('[name="servizio"]')?.value || '';
      const budget = form.querySelector('[name="budget"]')?.value || '';
      const tempistica = form.querySelector('[name="tempistica"]')?.value || '';
      const messaggio = form.querySelector('[name="messaggio"]')?.value || '';

      const subject = encodeURIComponent("Richiesta dal sito VA Digital");
      const body = encodeURIComponent(
`Nome: ${nome}
Email: ${email}
Servizio: ${servizio}
Budget: ${budget}
Tempistica: ${tempistica}

Messaggio:
${messaggio}
`);

      window.location.href = `mailto:atturo.vincenzo@gmail.com?subject=${subject}&body=${body}`;
    });
  }

  /* ===========================
     Sticky nav
     - Mobile (<=560): sempre visibile
     - Desktop: visibile solo dopo hero
     =========================== */
  function initStickyNav() {
    const bar = $(".sticky-nav");
    if (!bar) return;

    // inizializza una sola volta
    if (bar.dataset.inited === "1") return;
    bar.dataset.inited = "1";

    const sentinel = $("#hero-sentinel");

    const mqMobile = window.matchMedia("(max-width: 560px)");

    let rafId = null;
    let onScroll = null;
    let onResize = null;

    function setVisible(show){
      bar.classList.toggle("is-visible", show);
      document.body.classList.toggle("has-sticky", show);
      bar.setAttribute("aria-hidden", String(!show));
    }

    function computeDesktop(){
      if (!sentinel) {
        // fallback: se manca sentinel, la teniamo visibile
        setVisible(true);
        return;
      }
      const rect = sentinel.getBoundingClientRect();
      setVisible(rect.top <= 0);
    }

    function scheduleCompute(){
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        computeDesktop();
      });
    }

    function enableMobile(){
      // in mobile: sempre visibile e stop listener desktop
      teardownDesktop();
      setVisible(true);
    }

    function enableDesktop(){
      // in desktop: parte nascosta e si aggiorna con scroll/resize
      // (così non la vedi dentro l'hero)
      setVisible(false);
      computeDesktop();

      onScroll = () => scheduleCompute();
      onResize = () => scheduleCompute();

      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("resize", onResize, { passive: true });
      window.addEventListener("load", scheduleCompute, { passive: true });
    }

    function teardownDesktop(){
      if (onScroll) window.removeEventListener("scroll", onScroll);
      if (onResize) window.removeEventListener("resize", onResize);
      onScroll = null;
      onResize = null;

      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    }

    function applyMode(){
      if (mqMobile.matches) enableMobile();
      else enableDesktop();
    }

    mqMobile.addEventListener?.("change", applyMode);
    applyMode();
  }

  /* ===========================
     Bootstrap (include-ready)
     =========================== */
  function initAll(){
    initMenu();
    initDropdowns();
    initContactForm();
    initStickyNav();
  }

  document.addEventListener("DOMContentLoaded", initAll);
  document.addEventListener("va:includes:ready", initAll);
  window.addEventListener("load", initAll);

})();
