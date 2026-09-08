/* Math captcha refresh runtime.
   Wires the ↻ button next to the captcha image to POST /math-captcha/refresh/,
   swap the image + hidden token in-place, and clear the answer input.
   Load on any page that renders a `.math-captcha` widget (contact form, auth
   pages, etc). Idempotent — safe to include when no captcha exists on the page. */
(function () {
    'use strict';

    function getCsrf() {
        const cookie = document.cookie.split(';').find(function (c) {
            return c.trim().indexOf('csrftoken=') === 0;
        });
        if (cookie) return decodeURIComponent(cookie.trim().slice('csrftoken='.length));
        const hidden = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return hidden ? hidden.value : '';
    }

    function initCaptchaRefresh() {
        document.querySelectorAll('.math-captcha').forEach(function (wrap) {
            // Guard: skip if this widget was already initialised by a previous
            // script include (avoids double-listeners on auth pages).
            if (wrap.dataset.captchaBound === '1') return;
            wrap.dataset.captchaBound = '1';

            const btn = wrap.querySelector('[data-captcha-refresh]');
            const img = wrap.querySelector('[data-captcha-image]');
            // The hidden token input sits OUTSIDE the .math-captcha wrap (it's
            // rendered by the captcha_token widget), so search the whole form.
            const form = wrap.closest('form') || document;
            const hidden = form.querySelector('input[name="captcha_token"]');
            const refreshUrl = wrap.dataset.refreshUrl;
            if (!btn || !img || !hidden || !refreshUrl) return;

            btn.addEventListener('click', function () {
                btn.disabled = true;
                btn.classList.add('is-loading');

                fetch(refreshUrl, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'X-CSRFToken': getCsrf(),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                })
                    .then(function (res) {
                        if (!res.ok) throw new Error('refresh failed');
                        return res.json();
                    })
                    .then(function (data) {
                        // Cache-bust the <img> so the browser fetches the new PNG.
                        img.src = data.image_url + '?t=' + Date.now();
                        hidden.value = data.token;
                        const input = wrap.querySelector('.math-captcha__input');
                        if (input) { input.value = ''; input.focus(); }
                    })
                    .catch(function () { /* silent — user can try again */ })
                    .finally(function () {
                        btn.disabled = false;
                        btn.classList.remove('is-loading');
                    });
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCaptchaRefresh);
    } else {
        initCaptchaRefresh();
    }
})();
