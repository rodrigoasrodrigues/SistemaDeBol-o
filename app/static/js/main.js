/* =========================================================
   Bolão Copa 2026 – main.js
   Dark/light theme toggle with localStorage persistence
   ========================================================= */

(function () {
  'use strict';

  const html = document.documentElement;
  const btn = document.getElementById('theme-toggle');
  const icon = document.getElementById('theme-icon');
  const STORAGE_KEY = 'bolao-theme';

  function applyTheme(theme) {
    html.setAttribute('data-bs-theme', theme);
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    }
    if (btn) {
      btn.title = theme === 'dark' ? 'Modo claro' : 'Modo escuro';
    }
  }

  // Load stored preference or default to light
  const stored = localStorage.getItem(STORAGE_KEY) || 'light';
  applyTheme(stored);

  if (btn) {
    btn.addEventListener('click', function () {
      const current = html.getAttribute('data-bs-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem(STORAGE_KEY, next);
    });
  }

  // Auto-dismiss alerts after 5 s
  document.querySelectorAll('.alert.alert-dismissible').forEach(function (el) {
    setTimeout(function () {
      var bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 5000);
  });
})();
