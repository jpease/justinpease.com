// Keeps the end of the copyright range at the current year. The build writes
// the latest content year as the no-JS fallback.
document.querySelectorAll("[data-current-year]").forEach(function (el) {
  el.textContent = new Date().getFullYear();
});
