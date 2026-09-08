/* Blog form: live cover preview + minor UX polish.
   Server-side validators are the source of truth; this only wires the
   image preview and swaps the picker label so the user sees a live cover. */
(function () {
    'use strict';

    function initCoverPreview() {
        const input = document.getElementById('id_image');
        const preview = document.getElementById('blogCoverPreview');
        if (!input || !preview) return;

        input.addEventListener('change', function (e) {
            const file = e.target.files && e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function (ev) {
                let img = document.getElementById('blogCoverImg');
                if (!img) {
                    preview.innerHTML = '';
                    img = document.createElement('img');
                    img.id = 'blogCoverImg';
                    img.alt = 'پیش‌نمایش تصویر شاخص';
                    preview.appendChild(img);
                }
                img.src = ev.target.result;
                preview.dataset.hasImage = '1';

                const picker = document.querySelector('.blg-form__cover-picker span');
                if (picker) picker.textContent = 'تعویض تصویر';
            };
            reader.readAsDataURL(file);
        });
    }

    function init() {
        initCoverPreview();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
