/* Init per-tile Swiper sliders with pagination + subtle autoplay. */
(function () {
    'use strict';

    function initSliders(scope) {
        const sliders = (scope || document).querySelectorAll('.gallery-swiper:not(.is-swiper-init)');
        sliders.forEach(function (el) {
            el.classList.add('is-swiper-init');
            new Swiper(el, {
                loop: true,
                slidesPerView: 1,
                spaceBetween: 0,
                autoplay: { delay: 4200, disableOnInteraction: false, pauseOnMouseEnter: true },
                pagination: { el: el.querySelector('.swiper-pagination'), clickable: true },
                navigation: {
                    nextEl: el.querySelector('.swiper-button-next'),
                    prevEl: el.querySelector('.swiper-button-prev'),
                },
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { initSliders(); });
    } else {
        initSliders();
    }

    // Expose for load-more script to init newly added tiles.
    window.__galleryInitSliders = initSliders;
})();
