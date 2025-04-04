document.addEventListener('DOMContentLoaded', function () {
    const submitBtn = document.querySelector('#submitBtn');
    const resendBtn = document.querySelector('#resendBtn');
    const resendText = document.querySelector('#resendText');

    // غیرفعال کردن دکمه تأیید هنگام ارسال
    document.querySelector('#otpForm').addEventListener('submit', function () {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>در حال بررسی...';
    });

    // تایمر زنده برای ارسال مجدد
    document.querySelector('#resendForm').addEventListener('submit', function (e) {
        resendBtn.disabled = true;
        resendText.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>در حال ارسال...';
    });

    // دریافت مقدار remaining_seconds از data attribute
    const remainingSeconds = parseInt(resendBtn.getAttribute('data-remaining-seconds')) || 0;

    // شروع تایمر اگر remaining_seconds بزرگ‌تر از 0 باشد
    if (remainingSeconds > 0) {
        let timeLeft = remainingSeconds;
        resendBtn.disabled = true;
        resendText.textContent = `صبر کنید (${timeLeft} ثانیه)`;

        const timer = setInterval(() => {
            timeLeft--;
            resendText.textContent = `صبر کنید (${timeLeft} ثانیه)`;
            if (timeLeft <= 0) {
                clearInterval(timer);
                resendBtn.disabled = false;
                resendText.textContent = 'ارسال مجدد کد';
            }
        }, 1000);
    }
});