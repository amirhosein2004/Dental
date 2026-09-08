/* Toast messages — auto-dismiss + pause on hover + manual close. */
(function () {
    'use strict';

    const AUTO_DISMISS_MS = 5000;

    function dismiss(toast) {
        if (toast.dataset.leaving) return;
        toast.dataset.leaving = '1';
        toast.classList.add('is-leaving');
        toast.addEventListener('animationend', function () { toast.remove(); }, { once: true });
    }

    function initToast(toast) {
        const close = toast.querySelector('[data-toast-close]');
        const progress = toast.querySelector('.toast__progress');
        let timer = null;
        let remaining = AUTO_DISMISS_MS;
        let startedAt = 0;

        function start() {
            startedAt = performance.now();
            timer = setTimeout(function () { dismiss(toast); }, remaining);
            if (progress) progress.style.animationPlayState = 'running';
        }
        function pause() {
            if (!timer) return;
            clearTimeout(timer);
            timer = null;
            remaining -= performance.now() - startedAt;
            if (progress) progress.style.animationPlayState = 'paused';
        }

        toast.addEventListener('mouseenter', pause);
        toast.addEventListener('mouseleave', start);
        toast.addEventListener('focusin', pause);
        toast.addEventListener('focusout', start);

        if (close) {
            close.addEventListener('click', function () {
                if (timer) clearTimeout(timer);
                dismiss(toast);
            });
        }

        start();
    }

    function init() {
        document.querySelectorAll('[data-toast]').forEach(initToast);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
