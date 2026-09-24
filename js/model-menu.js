(() => {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector(".v2-menu-toggle");
    const menu = document.querySelector(".v2-menu");
    if (!button || !menu) return;

    if (!menu.querySelector('a[href="/pages/casi-studio.html"]')) {
      const caseStudiesLink = document.createElement("a");
      caseStudiesLink.href = "/pages/casi-studio.html";
      caseStudiesLink.textContent = "Casi studio";
      const projectsLink = menu.querySelector('a[href="#progetti"]');
      projectsLink?.insertAdjacentElement("afterend", caseStudiesLink);
    }

    if (!menu.querySelector('a[href="/pages/guide.html"]')) {
      const guideLink = document.createElement("a");
      guideLink.href = "/pages/guide.html";
      guideLink.textContent = "Guide";
      const packagesLink = menu.querySelector('a[href="/pages/pacchetti.html"]');
      menu.insertBefore(guideLink, packagesLink || menu.querySelector(".model-contact"));
    }

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
