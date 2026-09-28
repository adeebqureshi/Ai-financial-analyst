(function () {
  try {
    var key = "afa-theme";
    var fallback = "light";
    var stored = window.localStorage.getItem(key);
    var theme = stored === "light" || stored === "dark" ? stored : fallback;
    var root = document.documentElement;

    root.classList.toggle("dark", theme === "dark");
    root.style.colorScheme = theme;
  } catch {
    /* theme initialisation is best effort */
  }
})();
