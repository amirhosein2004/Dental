/* Gallery uploader — drag/drop + click, live thumbnails + remove-per-file,
   size summary, drop-zone highlight state. Works for both `add_gallery`
   (large form) and `update_gallery`'s compact upload panel.

   Native <input type="file"> replaces its FileList on every click, so
   selecting a second batch would drop the first. We keep our own accumulator
   (`state.files`) and mirror it back into input.files via DataTransfer so
   the browser sees every picked/dropped image on submit. */
(function () {
    'use strict';

    function formatSize(bytes) {
        if (!bytes) return '0 KB';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }

    function fileKey(f) {
        // Cheap dedup key: name + size + lastModified. Prevents users from
        // adding the exact same file twice in one submit.
        return f.name + '|' + f.size + '|' + f.lastModified;
    }

    function syncInput(input, files) {
        const dt = new DataTransfer();
        files.forEach(function (f) { dt.items.add(f); });
        input.files = dt.files;
    }

    function initZone(zone) {
        const input = zone.querySelector('[data-gal-file]');
        const grid = zone.querySelector('[data-gal-previews]');
        const emptyNote = grid ? grid.querySelector('[data-gal-empty]') : null;
        const summary = zone.querySelector('[data-gal-summary]');
        const countEl = zone.querySelector('[data-gal-count]');
        const sizeEl = zone.querySelector('[data-gal-size]');
        if (!input || !grid) return;

        const state = { files: [] };

        function render() {
            grid.querySelectorAll('.gal-preview').forEach(function (el) { el.remove(); });
            if (emptyNote) emptyNote.hidden = state.files.length > 0;

            if (state.files.length === 0) {
                if (summary) summary.hidden = true;
                return;
            }

            let total = 0;
            state.files.forEach(function (file, idx) {
                total += file.size;

                const tile = document.createElement('div');
                tile.className = 'gal-preview';

                const img = document.createElement('img');
                img.alt = file.name;
                tile.appendChild(img);

                const caption = document.createElement('span');
                caption.className = 'gal-preview__caption';
                caption.textContent = file.name;
                tile.appendChild(caption);

                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'gal-preview__remove';
                removeBtn.setAttribute('aria-label', 'حذف تصویر از انتخاب');
                removeBtn.innerHTML = '<i class="fas fa-xmark"></i>';
                removeBtn.addEventListener('click', function () {
                    state.files.splice(idx, 1);
                    syncInput(input, state.files);
                    render();
                });
                tile.appendChild(removeBtn);

                const reader = new FileReader();
                reader.onload = function (e) { img.src = e.target.result; };
                reader.readAsDataURL(file);

                grid.appendChild(tile);
            });

            if (summary) {
                summary.hidden = false;
                if (countEl) countEl.textContent = state.files.length;
                if (sizeEl) sizeEl.textContent = formatSize(total);
            }
        }

        function addPicked(list) {
            if (!list || list.length === 0) return;
            const seen = new Set(state.files.map(fileKey));
            Array.from(list).forEach(function (f) {
                if (!f.type.startsWith('image/')) return;
                if (seen.has(fileKey(f))) return;
                state.files.push(f);
                seen.add(fileKey(f));
            });
            syncInput(input, state.files);
            render();
        }

        input.addEventListener('change', function () {
            // Copy off the browser-provided FileList before we overwrite it
            // via DataTransfer, otherwise the reference is gone.
            const picked = Array.from(input.files || []);
            addPicked(picked);
        });

        // Drag & drop highlight + file assignment
        ['dragenter', 'dragover'].forEach(function (ev) {
            zone.addEventListener(ev, function (e) {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('is-dragging');
            });
        });
        ['dragleave', 'dragend', 'drop'].forEach(function (ev) {
            zone.addEventListener(ev, function (e) {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('is-dragging');
            });
        });
        zone.addEventListener('drop', function (e) {
            const dropped = e.dataTransfer && e.dataTransfer.files;
            addPicked(dropped);
        });
    }

    function init() {
        document.querySelectorAll('[data-gal-dropzone]').forEach(initZone);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
