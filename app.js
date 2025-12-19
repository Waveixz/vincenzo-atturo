/* app.js — VA Digital
   Menu tondo accessibile: toggle, aria, Esc, trap focus, click fuori, resize reset.
*/

(() => {
  const BREAKPOINT = 900; // px (deve combaciare con il tuo CSS)

  const btn  = document.querySelector('.menu-toggle');
  const menu = document.getElementById('menu');
  if (!btn || !menu) return;

  // Tutti i link cliccabili nel menu
  const links = Array.from(menu.querySelectorAll('a[href]'));

  // Media query per capire quando siamo in “mobile”
  const mqlMobile = window.matchMedia(`(max-width: ${BREAKPOINT}px)`);

  let prevFocused = null;
  let keydownBound = null;
  let clickOutsideBound = null;

  // --- API interne ---

  function isOpen() {
    return menu.classList.contains('open');
  }

  function openMenu() {
    if (isOpen()) return;
    prevFocused = document.activeElement;

    menu.classList.add('open');
    btn.setAttribute('aria-expanded', 'true');

    // Sposta il focus al primo link per l'uso da tastiera
    if (links.length) links[0].focus();

    // Listener globali
    keydownBound = onKeydown.bind(null);
    clickOutsideBound = onClickOutside.bind(null);
    document.addEventListener('keydown', keydownBound, true);
    document.addEventListener('click', clickOutsideBound, true);
  }

  function closeMenu({ restoreFocus = true } = {}) {
    if (!isOpen()) return;

    menu.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');

    // Ripristina il focus sul bottone (se richiesto)
    if (restoreFocus && btn) btn.focus();

    // Rimuovi listener globali
    if (keydownBound) document.removeEventListener('keydown', keydownBound, true);
    if (clickOutsideBound) document.removeEventListener('click', clickOutsideBound, true);
    keydownBound = null;
    clickOutsideBound = null;
  }

  function toggleMenu() {
    isOpen() ? closeMenu() : openMenu();
  }

  // --- Gestione eventi ---

  function onKeydown(e) {
    // ESC chiude
    if (e.key === 'Escape') {
      e.preventDefault();
      closeMenu();
      return;
    }

    // Trap focus dentro il menu solo quando è aperto e in mobile
    if (!isOpen() || !mqlMobile.matches || links.length === 0) return;

    if (e.key === 'Tab') {
      const first = links[0];
      const last  = links[links.length - 1];

      // Ciclo del focus tra primo e ultimo
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  function onClickOutside(e) {
    if (!isOpen()) return;

    const clickInsideMenu = menu.contains(e.target);
    const clickOnButton   = btn.contains(e.target);
    if (!clickInsideMenu && !clickOnButton) {
      closeMenu({ restoreFocus: false });
    }
  }

  // Chiudi menu quando si clicca un link del menu (UX migliore su mobile)
  links.forEach(a =>
    a.addEventListener('click', () => {
      if (mqlMobile.matches) closeMenu({ restoreFocus: false });
    })
  );

  // Reset stato quando si passa a desktop (>= BREAKPOINT)
  function onViewportChange() {
    if (!mqlMobile.matches) {
      // Siamo su desktop: assicura menu chiuso e aria coerente
      closeMenu({ restoreFocus: false });
    }
  }
  mqlMobile.addEventListener('change', onViewportChange);

  // Click sul bottone
  btn.addEventListener('click', toggleMenu);

  // Accessibilità: tastiera (Enter/Space) già gestita da <button>,
  // non serve intercettare keydown per il bottone.

  // Sanitizza stato iniziale
  closeMenu({ restoreFocus: false });
})();

(() => {
  document.querySelectorAll("[data-dd]").forEach(dd => {
    const btn = dd.querySelector(".va-dd__btn");
    const list = dd.querySelector(".va-dd__list");
    const valueEl = dd.querySelector("[data-dd-value]");
    const hidden = dd.querySelector('input[type="hidden"][name="pacchetto"]');
    const items = [...dd.querySelectorAll(".va-dd__item")];

    function open(){
      dd.classList.add("is-open");
      btn.setAttribute("aria-expanded","true");
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

    btn.addEventListener("click", () => dd.classList.contains("is-open") ? close() : open());

    items.forEach(it => {
      it.addEventListener("click", () => setValue(it.dataset.value));
      it.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setValue(it.dataset.value); }
      });
    });

    document.addEventListener("click", (e) => {
      if (!dd.contains(e.target)) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });
  });

  /* Precompila da data-package (riusa la tua logica) */
  document.querySelectorAll("[data-package]").forEach(btn => {
    btn.addEventListener("click", () => {
      const pkg = btn.getAttribute("data-package")?.trim();
      if (!pkg) return;

      const hidden = document.querySelector('input[name="pacchetto"]');
      const valueEl = document.querySelector("[data-dd-value]");
      const dd = document.querySelector("[data-dd]");
      if (hidden && valueEl) {
        hidden.value = pkg;
        valueEl.textContent = pkg;
        if (dd) {
          dd.querySelectorAll(".va-dd__item").forEach(it => {
            it.classList.toggle("is-selected", it.dataset.value === pkg);
          });
        }
      }
    });
  });
})();

document.getElementById("contact-form").addEventListener("submit", function(e){
  e.preventDefault();

  const form = e.target;

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

  const mailto = `mailto:atturo.vincenzo@gmail.com?subject=${subject}&body=${body}`;

  window.location.href = mailto;
});