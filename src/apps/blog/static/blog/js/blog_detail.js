/* Blog detail: copy-link share button (falls back to legacy execCommand). */
(function () {
    'use strict';

    function flashCopied(btn) {
        btn.classList.add('is-copied');
        const original = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(function () {
            btn.classList.remove('is-copied');
            btn.innerHTML = original;
        }, 1500);
    }

    function copyLink(btn) {
        const url = btn.dataset.url || window.location.href;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url).then(function () { flashCopied(btn); });
            return;
        }
        // Fallback for old browsers
        const ta = document.createElement('textarea');
        ta.value = url;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); flashCopied(btn); } catch (e) { /* silent */ }
        document.body.removeChild(ta);
    }

    function init() {
        document.querySelectorAll('[data-post-copy]').forEach(function (btn) {
            btn.addEventListener('click', function () { copyLink(btn); });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
