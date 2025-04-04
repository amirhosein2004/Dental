document.addEventListener('DOMContentLoaded', () => {
    // بخش اسلایدر بنر
    const bannerContainer = document.querySelector('.banner-container');
    const bannerItems = document.querySelectorAll('.banner-item');
    const prevButton = document.querySelector('.banner-nav--prev');
    const nextButton = document.querySelector('.banner-nav--next');
    const dots = document.querySelectorAll('.banner-dot');
    let currentIndex = 0;
    let autoSlideInterval;

    // توابع اسلایدر
    function showSlide(index) {
        bannerItems.forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
        currentIndex = index;
        console.log(`اسلاید فعال: ${index}`);
    }

    function nextSlide() {
        currentIndex = (currentIndex + 1) % bannerItems.length;
        showSlide(currentIndex);
    }

    function prevSlide() {
        currentIndex = (currentIndex - 1 + bannerItems.length) % bannerItems.length;
        showSlide(currentIndex);
    }

    // کنترل پخش خودکار
    function startAutoSlide() {
        autoSlideInterval = setInterval(nextSlide, 5000);
        console.log('پخش خودکار شروع شد');
    }

    function stopAutoSlide() {
        clearInterval(autoSlideInterval);
        console.log('پخش خودکار متوقف شد');
    }

    // رویدادهای دکمه‌ها
    nextButton.addEventListener('click', () => {
        stopAutoSlide();
        nextSlide();
        startAutoSlide();
    });

    prevButton.addEventListener('click', () => {
        stopAutoSlide();
        prevSlide();
        startAutoSlide();
    });

    // رویداد نقاط ناوبری
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            stopAutoSlide();
            showSlide(index);
            startAutoSlide();
        });
    });

    // بخش اسلایدر خودکار ساده
    let currentPosition = 0;
    const bannerWidth = bannerContainer.offsetWidth;
    let slideInterval;

    function autoSlide() {
        if (bannerItems.length > 1) {
            currentPosition += bannerWidth;
            if (currentPosition >= bannerWidth * bannerItems.length) {
                currentPosition = 0;
            }
            bannerContainer.scrollTo({
                left: currentPosition,
                behavior: 'smooth'
            });
        }
    }

    // راه‌اندازی اسلایدرها
    if (bannerItems.length > 0) {
        console.log(`تعداد بنرها: ${bannerItems.length}`);
        showSlide(currentIndex);
        startAutoSlide();
        slideInterval = setInterval(autoSlide, 3000);

        // رویدادهای هاور
        bannerContainer.addEventListener('mouseenter', () => {
            stopAutoSlide();
            clearInterval(slideInterval);
        });

        bannerContainer.addEventListener('mouseleave', () => {
            startAutoSlide();
            slideInterval = setInterval(autoSlide, 3000);
        });

        // هماهنگی اسکرول دستی
        bannerContainer.addEventListener('scroll', () => {
            currentPosition = Math.round(bannerContainer.scrollLeft / bannerWidth) * bannerWidth;
        });
    } else {
        console.warn('هیچ بنری برای نمایش یافت نشد.');
    }
});