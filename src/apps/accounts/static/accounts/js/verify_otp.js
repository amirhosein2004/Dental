/* OTP verification: submit-button spinner + resend cooldown timer.
   Password toggle + captcha refresh are handled by login.js on the same
   page — keep this script focused on OTP-specific behaviour. */
(function () {
    'use strict';

    function init() {
        const submitBtn = document.getElementById('submitBtn');
        const otpForm = document.getElementById('otpForm');
        const resendForm = document.getElementById('resendForm');
        const resendBtn = document.getElementById('resendBtn');
        const resendText = document.getElementById('resendText');

        if (otpForm && submitBtn) {
            otpForm.addEventListener('submit', function () {
                submitBtn.disabled = true;
                submitBtn.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i>' +
                    '<span>در حال بررسی...</span>';
            });
        }

        if (resendForm && resendBtn && resendText) {
            resendForm.addEventListener('submit', function () {
                resendBtn.disabled = true;
                resendText.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i>' +
                    '<span> در حال ارسال...</span>';
            });

            const remaining = parseInt(resendBtn.getAttribute('data-remaining-seconds'), 10) || 0;
            if (remaining > 0) {
                let timeLeft = remaining;
                resendBtn.disabled = true;
                resendText.textContent = 'ارسال مجدد (' + timeLeft + ' ثانیه)';

                const timer = setInterval(function () {
                    timeLeft -= 1;
                    if (timeLeft <= 0) {
                        clearInterval(timer);
                        resendBtn.disabled = false;
                        resendText.textContent = 'ارسال مجدد کد';
                    } else {
                        resendText.textContent = 'ارسال مجدد (' + timeLeft + ' ثانیه)';
                    }
                }, 1000);
            }
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
