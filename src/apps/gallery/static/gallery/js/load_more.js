/* Gallery masonry "load more".

   The endpoint returns server-rendered tile HTML (see LoadMoreGalleriesView),
   so this file only appends it and re-inits Swiper on the new tiles. The old
   version rebuilt tiles in JS using the pre-redesign Bootstrap markup and
   appended them to a `.row.g-4` container that no longer exists — the button
   silently did nothing. */
(function () {
    'use strict';

    function init() {
        const button = document.getElementById('load-more');
        const container = document.getElementById('gal-masonry');
        const endNote = document.getElementById('no-more-galleries');
        if (!button || !container) return;

        const label = button.querySelector('span');
        const originalLabel = label ? label.textContent : '';

        function setBusy(busy) {
            button.disabled = busy;
            if (label) label.textContent = busy ? 'در حال بارگذاری…' : originalLabel;
        }

        function finish() {
            button.hidden = true;
            if (endNote) endNote.hidden = false;
        }

        button.addEventListener('click', function () {
            const offset = parseInt(button.dataset.offset, 10) || 0;

            // Preserve the active category/doctor filter from the URL so paging
            // walks the filtered set.
            const params = new URLSearchParams(window.location.search);
            params.set('offset', offset);

            setBusy(true);
            fetch(button.dataset.url + '?' + params.toString(), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
                .then(function (response) {
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    return response.json();
                })
                .then(function (data) {
                    if (data.count) {
                        container.insertAdjacentHTML('beforeend', data.html);
                        // Swiper must be attached to the tiles we just inserted.
                        if (window.__galleryInitSliders) {
                            window.__galleryInitSliders(container);
                        }
                    }
                    // Advance past rows consumed server-side, including empty
                    // galleries that produced no tile.
                    button.dataset.offset = offset + (data.consumed || data.count || 0);

                    if (!data.has_more) finish();
                })
                .catch(function (error) {
                    console.error('خطا در بارگذاری گالری‌ها:', error);
                })
                .finally(function () {
                    setBusy(false);
                });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
