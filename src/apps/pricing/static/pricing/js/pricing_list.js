/* Pricing — inline live search across grouped items. Hides empty groups. */
(function () {
    'use strict';

    function normalize(value) {
        return (value || '')
            .toString()
            .trim()
            .toLowerCase()
            .replace(/ی/g, 'ي')
            .replace(/ک/g, 'ك');
    }

    function init() {
        const input = document.getElementById('prc-search');
        const emptySearch = document.getElementById('prc-empty-search');
        if (!input) return;

        const cards = Array.from(document.querySelectorAll('.prc-card[data-prc-title]'));
        const sections = Array.from(document.querySelectorAll('.prc-section'));

        function apply() {
            const q = normalize(input.value);
            let totalVisible = 0;

            sections.forEach(function (section) {
                const items = section.querySelectorAll('.prc-card');
                let sectionVisible = 0;
                items.forEach(function (card) {
                    const title = normalize(card.dataset.prcTitle);
                    const category = normalize(card.dataset.prcCategory);
                    const match = !q || title.indexOf(q) !== -1 || (category && category.indexOf(q) !== -1);
                    card.classList.toggle('is-hidden', !match);
                    if (match) sectionVisible += 1;
                });
                section.classList.toggle('is-hidden', q && sectionVisible === 0);
                totalVisible += sectionVisible;
            });

            if (emptySearch) emptySearch.hidden = !q || totalVisible > 0;
        }

        input.addEventListener('input', apply);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
