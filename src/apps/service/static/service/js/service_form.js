/* Service form: live cover preview, and the FAQ rows the writer adds. */
(function () {
    'use strict';

    /* ---------------------------------------------------------- cover ---- */
    function initCover() {
        const input = document.getElementById('id_image');
        const preview = document.getElementById('serviceCoverPreview');
        if (!input || !preview) return;

        input.addEventListener('change', function (e) {
            const file = e.target.files && e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function (ev) {
                let img = document.getElementById('serviceCoverImg');
                if (!img) {
                    preview.innerHTML = '';
                    img = document.createElement('img');
                    img.id = 'serviceCoverImg';
                    img.alt = 'پیش‌نمایش تصویر';
                    preview.appendChild(img);
                }
                img.src = ev.target.result;

                const picker = document.querySelector('.svc-form__cover-picker span');
                if (picker) picker.textContent = 'تعویض تصویر';
            };
            reader.readAsDataURL(file);
        });
    }

    /* ------------------------------------------------------------ FAQ ---- */
    /*
     * The formset renders with `extra=0`, so the block opens with exactly the
     * questions the treatment already has. This adds one row at a time from
     * `empty_form`, which is the only reason a writer can enter more than the
     * number of questions the server happened to send.
     *
     * Removing an unsaved row clears its inputs and hides it rather than
     * detaching the node: a blank row is ignored on save, whereas a removed
     * node would leave a gap in the `faqs-N-` indexes and Django reads that
     * as a tampered ManagementForm.
     */
    function initFaq() {
        const rows = document.getElementById('svcFaqRows');
        const addBtn = document.getElementById('svcFaqAdd');
        const template = document.getElementById('svcFaqTemplate');
        const totalInput = document.getElementById('id_faqs-TOTAL_FORMS');
        const emptyNote = document.getElementById('svcFaqEmpty');
        if (!rows || !addBtn || !template || !totalInput) return;

        function visibleRows() {
            return Array.prototype.filter.call(
                rows.querySelectorAll('[data-faq-row]'),
                function (row) { return !row.hidden; }
            );
        }

        function renumber() {
            visibleRows().forEach(function (row, i) {
                const badge = row.querySelector('[data-faq-num]');
                if (badge) badge.textContent = String(i + 1);
            });
            if (emptyNote) emptyNote.hidden = visibleRows().length > 0;
        }

        function addRow() {
            const index = parseInt(totalInput.value, 10) || 0;
            const html = template.innerHTML.replace(/__prefix__/g, String(index));

            const holder = document.createElement('div');
            holder.innerHTML = html.trim();
            const row = holder.firstElementChild;
            if (!row) return;

            rows.appendChild(row);
            totalInput.value = String(index + 1);
            renumber();

            const first = row.querySelector('input[type="text"], textarea');
            if (first) first.focus();
        }

        function dropRow(row) {
            row.querySelectorAll('input, textarea, select').forEach(function (field) {
                // The hidden `id` must keep its value on a saved row; those
                // rows use the DELETE checkbox instead and never reach here.
                if (field.type === 'checkbox' || field.type === 'radio') {
                    field.checked = false;
                } else if (field.type !== 'hidden') {
                    field.value = '';
                }
            });
            row.hidden = true;
            renumber();
        }

        addBtn.addEventListener('click', addRow);

        // Delegated: rows added after load carry the same button.
        rows.addEventListener('click', function (e) {
            const btn = e.target.closest('[data-faq-drop]');
            if (!btn) return;
            const row = btn.closest('[data-faq-row]');
            if (row) dropRow(row);
        });

        renumber();
    }

    function init() {
        initCover();
        initFaq();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
