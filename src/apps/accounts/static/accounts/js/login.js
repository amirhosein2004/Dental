/* Auth-page runtime: password show/hide toggle.
   Captcha refresh has moved to `static/js/math_captcha.js` so any page that
   uses the captcha (contact form, auth pages) can share the same runtime.
   Both scripts are safe to load together — the captcha init is guarded by
   a `data-captcha-bound` flag. */
(function () {
    'use strict';

    function initPasswordToggles() {
        document.querySelectorAll('[data-pwd-toggle]').forEach(function (btn) {
            const wrap = btn.closest('.auth-form__password');
            if (!wrap) return;
            const input = wrap.querySelector('input[type="password"], input[type="text"]');
            if (!input) return;

            btn.addEventListener('click', function () {
                const isHidden = input.type === 'password';
                input.type = isHidden ? 'text' : 'password';
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-eye');
                    icon.classList.toggle('fa-eye-slash');
                }
                btn.setAttribute('aria-label', isHidden ? 'پنهان کردن رمز' : 'نمایش رمز');
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPasswordToggles);
    } else {
        initPasswordToggles();
    }
})();
