(() => {
  "use strict";

  const url = "https://va-digital.it/vincenzo-atturo/";
  const shareButton = document.querySelector("#share-card");
  const copyButton = document.querySelector("#copy-link");
  const status = document.querySelector("#share-status");

  const setStatus = (message) => {
    if (!status) return;
    status.textContent = message;
    window.setTimeout(() => {
      if (status.textContent === message) status.textContent = "";
    }, 3500);
  };

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setStatus("Link copiato. Ora puoi condividerlo dove preferisci.");
    } catch {
      window.prompt("Copia il link del biglietto digitale:", url);
    }
  };

  shareButton?.addEventListener("click", async () => {
    if (!navigator.share) {
      await copyLink();
      return;
    }

    try {
      await navigator.share({
        title: "Vincenzo Atturo | VA Digital",
        text: "Software, automazioni, dashboard, dati e GIS su misura.",
        url
      });
    } catch (error) {
      if (error.name !== "AbortError") await copyLink();
    }
  });

  copyButton?.addEventListener("click", copyLink);
})();
