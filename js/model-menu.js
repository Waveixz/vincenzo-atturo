(() => {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector(".v2-menu-toggle");
    const menu = document.querySelector(".v2-menu");
    if (!button || !menu) return;

    const close = () => {
      menu.classList.remove("open");
      button.classList.remove("open");
      button.setAttribute("aria-expanded", "false");
    };

    button.addEventListener("click", () => {
      const open = menu.classList.toggle("open");
      button.classList.toggle("open", open);
      button.setAttribute("aria-expanded", String(open));
    });

    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", close);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
  });
})();
