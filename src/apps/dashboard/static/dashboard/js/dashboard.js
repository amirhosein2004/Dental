/* dashboard.js — پنل پزشک
   Runtime for:
   1) Avatar preview when a new image is picked
   2) Password visibility toggles
   3) Native <dialog>-based delete confirmation
*/
(function () {
    'use strict';

    function initAvatarPreview() {
        var input = document.getElementById('id_image');
        var preview = document.getElementById('dshAvatarPreview');
        if (!input || !preview) return;

        input.addEventListener('change', function () {
            var file = input.files && input.files[0];
            if (!file) return;
            var reader = new FileReader();
            reader.onload = function (e) {
                // If the current placeholder is a <span> fallback, swap it for an <img>.
                if (preview.tagName !== 'IMG') {
                    var img = document.createElement('img');
                    img.id = 'dshAvatarPreview';
                    img.alt = 'پیش‌نمایش عکس پروفایل';
                    img.src = e.target.result;
                    preview.replaceWith(img);
                    preview = img;
                    return;
                }
                preview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    }

    function initPasswordToggles() {
        document.querySelectorAll('.dsh-form__pw-toggle').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var targetId = btn.getAttribute('data-target');
                var input = document.getElementById(targetId);
                if (!input) return;
                var icon = btn.querySelector('i');
                if (input.type === 'password') {
                    input.type = 'text';
                    if (icon) { icon.classList.remove('fa-eye'); icon.classList.add('fa-eye-slash'); }
                    btn.setAttribute('aria-label', 'مخفی کردن رمز');
                } else {
                    input.type = 'password';
                    if (icon) { icon.classList.remove('fa-eye-slash'); icon.classList.add('fa-eye'); }
                    btn.setAttribute('aria-label', 'نمایش رمز');
                }
            });
        });
    }

    function initDeleteDialog() {
        var dialog = document.getElementById('dshDeleteDialog');
        var form = document.getElementById('dshDeleteForm');
        var nameSlot = document.getElementById('dshDeleteName');
        if (!dialog || !form || !nameSlot) return;

        // Feature-detect <dialog>; fall back to native confirm() where unsupported.
        var supportsDialog = typeof dialog.showModal === 'function';

        document.querySelectorAll('[data-delete-url]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var url = btn.getAttribute('data-delete-url');
                var title = btn.getAttribute('data-delete-title') || 'این مورد';
                if (!url) return;

                if (!supportsDialog) {
                    if (window.confirm('حذف «' + title + '»؟')) {
                        form.action = url;
                        form.submit();
                    }
                    return;
                }
                form.action = url;
                nameSlot.textContent = title;
                dialog.showModal();
            });
        });

        var cancelBtn = dialog.querySelector('[data-dialog-cancel]');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function () { dialog.close(); });
        }
        // Click outside the form (on backdrop) also closes
        dialog.addEventListener('click', function (e) {
            if (e.target === dialog) dialog.close();
        });
    }

    function init() {
        initAvatarPreview();
        initPasswordToggles();
        initDeleteDialog();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
