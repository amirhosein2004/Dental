/*
 * Contact page behaviour: one Leaflet map per practice, plus form polish.
 *
 * The coordinates used to be two module-level constants — one clinic, one
 * marker. The practice has two locations in two cities, so the numbers now
 * come off each map container's `data-map-*` attributes, written by the
 * template from `Branch.latitude` / `Branch.longitude`. A branch with no
 * coordinates renders a note instead of a container, so it is simply absent
 * from this loop rather than dropping a marker at 0,0.
 *
 * Tiles: OpenStreetMap — free, reachable from Iran, no API key.
 */
(function () {
    'use strict';

    function initMaps() {
        if (typeof L === 'undefined') return;

        document.querySelectorAll('[data-map-lat][data-map-lng]').forEach(function (el) {
            const lat = parseFloat(el.dataset.mapLat);
            const lng = parseFloat(el.dataset.mapLng);
            if (!isFinite(lat) || !isFinite(lng)) return;

            const map = L.map(el, {
                attributionControl: true,
                center: [lat, lng],
                zoom: 15,
                zoomControl: true,
                // Two maps stacked on a phone: a one-finger drag must scroll
                // the page, not pan whichever map happens to be under it.
                scrollWheelZoom: false,
            });

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            }).addTo(map);

            L.marker([lat, lng]).addTo(map)
                .bindPopup(el.dataset.mapLabel || 'مکان مطب')
                .openPopup();

            // The container is laid out by CSS grid; Leaflet measures it at
            // construction time, which on a still-settling layout can be the
            // wrong size and leaves grey tiles.
            setTimeout(function () { map.invalidateSize(); }, 200);
        });
    }

    function initForm() {
        const form = document.querySelector('.needs-validation');
        if (!form) return;

        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add('was-validated');
            }
        }, false);

        form.querySelectorAll('.form-control').forEach(function (input) {
            input.addEventListener('blur', function () {
                if (!input.checkValidity() && !input.classList.contains('shake')) {
                    input.classList.add('shake');
                    setTimeout(function () { input.classList.remove('shake'); }, 300);
                }
            });
        });
    }

    function init() {
        initMaps();
        initForm();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
