/* Blog list "load more".

   The endpoint returns server-rendered card HTML (see LoadMoreBlogsView), so
   this file only appends it. Markup lives in `blog/_blog_card.html` alone —
   the old version re-templated cards here in JS and drifted out of sync with
   the redesign, producing unstyled Bootstrap leftovers. */
(function () {
    'use strict';

    function init() {
        const button = document.getElementById('load-more');
        const container = document.getElementById('blog-container');
        const endNote = document.getElementById('no-more-blogs');
        const filterForm = document.getElementById('blogFilterForm');
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

            // Carry the active filters so "load more" pages the filtered set,
            // not the unfiltered one.
            const params = new URLSearchParams(
                filterForm ? new FormData(filterForm) : ''
            );
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
                        button.dataset.offset = offset + data.count;
                    }
                    if (!data.has_more || !data.count) finish();
                })
                .catch(function (error) {
                    console.error('خطا در بارگذاری مقالات:', error);
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
