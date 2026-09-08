/* Services page — chip active-state (visual filter placeholder). */
(function () {
    'use strict';

    function init() {
        const chips = document.querySelectorAll('[data-svc-filter]');
        if (!chips.length) return;

        chips.forEach(function (chip) {
            chip.addEventListener('click', function () {
                chips.forEach(function (c) { c.classList.remove('is-active'); });
                chip.classList.add('is-active');
                // Real filter wiring will hook in once services carry a
                // category attribute. For now the chip is visual only.
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
