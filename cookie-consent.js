(() => {
  "use strict";

  const KEY = "va_cookie_consent_v1";

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY)); } catch { return null; }
  }
  function write(v) {
    try { localStorage.setItem(KEY, JSON.stringify(v)); } catch {}
  }

  function setGoogleConsent(consent) {
    if (typeof window.gtag !== "function") return;

    window.gtag("consent", "update", {
      analytics_storage: consent.analytics ? "granted" : "denied",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      functionality_storage: "granted",
      security_storage: "granted",
    });
  }

  function initCookieBanner() {
    const banner = document.getElementById("cookie-banner");
    if (!banner) {
      console.warn("[cookie] #cookie-banner non trovato");
      return;
    }

    const prefs = document.getElementById("cookie-prefs");
    const chkAnalytics = document.getElementById("cookie-analytics");

    const show = () => { banner.hidden = false; };
    const hide = () => {
      banner.hidden = true;
      if (prefs) prefs.hidden = true;
    };

    const apply = (consent) => {
      setGoogleConsent(consent);
      write(consent);
      hide();
    };

    // Stato iniziale
    const saved = read();
    if (saved) {
      setGoogleConsent(saved);
      hide();
    } else {
      show();
    }

    // Delegation: un solo listener per tutti i bottoni
    banner.addEventListener("click", (e) => {
      const el = e.target.closest("[data-cookie]");
      if (!el) {
        // click sullo sfondo (overlay) -> chiudi (opzionale)
        if (e.target === banner) hide();
        return;
      }

      e.preventDefault();

      const action = el.dataset.cookie;

      if (action === "close") return hide();                 // X
      if (action === "accept") return apply({ analytics: true });
      if (action === "reject") return apply({ analytics: false });

      if (action === "prefs") {
        if (prefs) prefs.hidden = !prefs.hidden;
        return;
      }

      if (action === "save") {
        return apply({ analytics: !!chkAnalytics?.checked });
      }
    });

    // API pubblica per footer: "Gestisci cookie"
    window.VA_openCookiePrefs = () => {
      show();
      if (prefs) prefs.hidden = false;
    };
  }

  // Se usi include -> init quando pronti
  document.addEventListener("va:includes:ready", initCookieBanner);

  // Fallback
  document.addEventListener("DOMContentLoaded", initCookieBanner);
})();
