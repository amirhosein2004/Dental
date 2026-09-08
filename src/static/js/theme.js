/* Theme toggle — light / dark with system fallback.
   Anti-FOUC init lives inline in <head>; this file wires the UI toggles. */

(function () {
    'use strict';

    const STORAGE_KEY = 'dental-theme';
    const root = document.documentElement;

    function currentEffectiveTheme() {
        const stored = root.getAttribute('data-theme');
        if (stored === 'dark' || stored === 'light') return stored;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme, persist) {
        root.setAttribute('data-theme', theme);
        if (persist) {
            try { localStorage.setItem(STORAGE_KEY, theme); } catch (_) { /* private mode */ }
        }
        updateToggles(theme);
    }

    function updateToggles(theme) {
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
            btn.setAttribute('aria-label', theme === 'dark' ? 'حالت روشن' : 'حالت تیره');
            const sun = btn.querySelector('[data-theme-icon="sun"]');
            const moon = btn.querySelector('[data-theme-icon="moon"]');
            if (sun && moon) {
                sun.style.display = theme === 'dark' ? '' : 'none';
                moon.style.display = theme === 'dark' ? 'none' : '';
            }
        });
    }

    function bindToggles() {
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const next = currentEffectiveTheme() === 'dark' ? 'light' : 'dark';
                applyTheme(next, true);
            });
        });
        updateToggles(currentEffectiveTheme());
    }

    // Follow OS changes when the user has not made an explicit choice.
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
        try {
            if (!localStorage.getItem(STORAGE_KEY)) {
                applyTheme(e.matches ? 'dark' : 'light', false);
            }
        } catch (_) {
            applyTheme(e.matches ? 'dark' : 'light', false);
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindToggles);
    } else {
        bindToggles();
    }
})();
