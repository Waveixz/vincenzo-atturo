/* includes.js — VA Digital
   - Inject partials (stikly/header/footer/cookie)
   - Cache in sessionStorage per ridurre flicker ("scatto")
   - Sblocco pagina con classi va-loading / va-ready
   - Evidenzia link attivo dopo header injection
   - Emette evento "va:includes:ready" SEMPRE (anche se un include fallisce)
*/

(() => {
  "use strict";

  const HTML = document.documentElement;

  function setReady() {
    HTML.classList.remove("va-loading");
    HTML.classList.add("va-ready");
  }

  function setActiveNavLink() {
    const path = location.pathname.replace(/\/$/, "");

    document.querySelectorAll(".nav-desktop a").forEach(a => {
      const href = new URL(a.getAttribute("href"), location.origin)
        .pathname.replace(/\/$/, "");
      a.classList.toggle("is-active", href === path);
    });
  }

  async function inject(selector, url) {
    const host = document.querySelector(selector);
    if (!host) return false;

    const key = "va:include:" + url;

    // 1) Mostra subito cache (se presente) per ridurre lo scatto
    const cached = sessionStorage.getItem(key);
    if (cached) host.innerHTML = cached;

    // 2) Poi fetch: aggiorna contenuto + cache
    const res = await fetch(url, { cache: "force-cache" });
    if (!res.ok) throw new Error(`Include fail: ${url} (${res.status})`);

    const html = await res.text();
    host.innerHTML = html;
    sessionStorage.setItem(key, html);

    return true;
  }

  async function init() {
    try {
      // Inietta solo se i placeholder esistono.
      // Ogni include è "indipendente": se uno fallisce gli altri continuano.
      await inject('[data-include="stikly"]', "/partials/stikly.html").catch(console.error);
      await inject('[data-include="header"]', "/partials/header.html").catch(console.error);
      await inject('[data-include="footer"]', "/partials/footer.html").catch(console.error);
      await inject('[data-include="cookie"]', "/partials/cookie.html").catch(console.error);

      // Anno automatico (footer)
      document.querySelectorAll("[data-year]").forEach(el => {
        el.textContent = String(new Date().getFullYear());
      });

      // Link attivo (solo ora che l'header esiste)
      setActiveNavLink();

    } finally {
      // Sblocca SEMPRE la pagina, anche se qualche include fallisce
      setReady();

      // Evento: include pronti (app.js / cookie-consent.js possono inizializzare qui)
      document.dispatchEvent(new Event("va:includes:ready"));
    }
  }

  init().catch(err => {
    console.error(err);
    // anti "pagina invisibile" se succede qualcosa di inatteso
    setReady();
    document.dispatchEvent(new Event("va:includes:ready"));
  });
})();
