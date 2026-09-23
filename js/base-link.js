(() => {
  const base = document.querySelector('meta[name="site-base"]')?.content || "/";
  document.querySelectorAll('[data-href]').forEach(a => {
    a.href = base + a.dataset.href;
  });
})();
