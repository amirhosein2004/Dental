document.addEventListener('DOMContentLoaded', function () {
    // پیدا کردن تمام اسلایدرها
    const sliders = document.querySelectorAll('.gallery-swiper');

    sliders.forEach(slider => {
        // تنظیمات Swiper برای هر گالری
        new Swiper(slider, {
            loop: true, // چرخش بی‌نهایت
            slidesPerView: 1, // نمایش یک اسلاید در هر زمان
            spaceBetween: 0, // حذف فاصله بین اسلایدها
            autoplay: { // حرکت خودکار
                delay: 3000, // تغییر اسلاید هر 3 ثانیه
                disableOnInteraction: false, // ادامه حرکت خودکار بعد از تعامل
            },
            navigation: {
                nextEl: '.swiper-button-next', // دکمه بعدی
                prevEl: '.swiper-button-prev', // دکمه قبلی
            },
            // واکنش‌گرایی (در صورت نیاز می‌تونید تنظیم کنید)
            breakpoints: {
                768: {
                    slidesPerView: 1,
                },
            },
        });
    });
});