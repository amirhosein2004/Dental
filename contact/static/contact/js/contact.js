// کد جاوااسکریپت برای انیمیشن متن‌های تزئینی و نقشه
var map = new L.Map('map', {
    attributionControl: false,
    key: 'web.567de89946f24e1ab41c2931720f1871',
    maptype: 'osm-bright',
    center: [37.106763111365744, 58.51246833914425],
    zoom: 15,
    zoomControl: true,
});

L.marker([37.106763111365744, 58.51246833914425]).addTo(map)
    .bindPopup('مکان مطب')
    .openPopup();

// بهینه‌سازی عملکرد با استفاده از DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    // 1. اعتبارسنجی فرم تماس
    const form = document.querySelector('.needs-validation');
    if (form) {
        form.addEventListener('submit', (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add('was-validated');
            }
        }, false);

        // اضافه کردن انیمیشن لرزش به فیلدهای نامعتبر هنگام فوکوس خارج شدن
        const inputs = form.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (!input.checkValidity() && !input.classList.contains('shake')) {
                    input.classList.add('shake');
                    setTimeout(() => input.classList.remove('shake'), 300); // همگام با انیمیشن CSS
                }
            });
        });
    }

    // 3. بهینه‌سازی عملکرد با Debounce برای رویدادهای هاور (اختیاری)
    const debounce = (func, wait) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    };

    // اعمال افکت هاور به دکمه‌ها با Debounce
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', debounce(() => {
            btn.classList.add('hover-scale');
        }, 100));
        btn.addEventListener('mouseleave', debounce(() => {
            btn.classList.remove('hover-scale');
        }, 100));
    });
});