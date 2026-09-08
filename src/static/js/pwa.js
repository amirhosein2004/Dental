/* Installable-app plumbing, loaded on every page.

   Two jobs:

   1. Register the service worker for everyone. It used to be registered only
      when a staff member switched notifications on, from the messages page —
      which meant a normal visitor never had one, and Chrome does not offer to
      install a site without a registered worker. Push needed the worker;
      installability needs it registered *up front*.

   2. Drive the install button. Chrome and Edge fire `beforeinstallprompt` once
      the site qualifies; the event is captured so the prompt can be shown from
      a real button instead of whenever the browser felt like it. Safari fires
      nothing at all — there the button explains the Share → Add to Home Screen
      route, which is the only way in on iOS and also the precondition for
      notifications there.

      The button used to stay hidden until that event arrived, which made it
      come and go: Chrome fires it once per qualifying visit and stops firing
      after the visitor dismisses the prompt or installs elsewhere, so the
      button simply vanished from the bar with nothing explaining why. It is
      now shown to anyone not already running the installed app, and falls
      back to the instructions dialog when there is no prompt to fire. */
(function () {
    'use strict';

    var SW_URL = '/sw.js';
    var deferredPrompt = null;

    function isIOS() {
        // iPadOS reports itself as a Mac, so the touch-point count is what
        // separates an iPad from a desktop Safari.
        return /iPad|iPhone|iPod/.test(navigator.userAgent) ||
            (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    }

    function isInstalled() {
        return window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone === true;
    }

    function registerWorker() {
        if (!('serviceWorker' in navigator) || !window.isSecureContext) return;

        // After load: registering during page load competes with the page's own
        // requests for bandwidth, and nothing here is needed for first paint.
        window.addEventListener('load', function () {
            navigator.serviceWorker.register(SW_URL, { scope: '/' })
                .catch(function (error) {
                    console.warn('service worker registration failed:', error);
                });
        });
    }

    function openInstructions() {
        var dialog = document.querySelector('#pwaInstallDialog');
        if (!dialog || typeof dialog.showModal !== 'function') return;

        // One dialog, two sets of steps: the Share-menu route on iOS, the
        // address-bar route everywhere else.
        var wanted = isIOS() ? 'ios' : 'other';
        dialog.querySelectorAll('[data-pwa-steps]').forEach(function (block) {
            block.hidden = block.getAttribute('data-pwa-steps') !== wanted;
        });
        dialog.showModal();
    }

    function setupInstallButton() {
        var button = document.querySelector('[data-pwa-install]');
        if (!button) return;

        // Already running as an app — offering to install it again is noise.
        if (isInstalled()) return;

        button.hidden = false;

        // iOS has no install event at all, so there is nothing to wait for.
        if (!isIOS()) {
            window.addEventListener('beforeinstallprompt', function (event) {
                // Stop Chrome's own mini-infobar; the button replaces it.
                event.preventDefault();
                deferredPrompt = event;
            });
        }

        button.addEventListener('click', function () {
            if (!deferredPrompt) {
                openInstructions();
                return;
            }
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then(function (choice) {
                // The event is single-use: Chrome will fire a fresh one if the
                // visitor declines and later qualifies again.
                deferredPrompt = null;
                if (choice.outcome === 'accepted') button.hidden = true;
            });
        });

        window.addEventListener('appinstalled', function () {
            deferredPrompt = null;
            button.hidden = true;
        });
    }

    registerWorker();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupInstallButton);
    } else {
        setupInstallButton();
    }
})();
