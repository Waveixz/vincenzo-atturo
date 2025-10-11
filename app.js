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