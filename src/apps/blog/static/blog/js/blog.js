document.addEventListener('DOMContentLoaded', function () {
    // غیرفعال کردن scroll restoration مرورگر
    if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
    }

    // چک کردن و حذف فیلترها با ریلود
    const url = new URL(window.location.href);
    const hasFilters = url.searchParams.size > 0;
    if (hasFilters && window.performance.navigation.type === 1) { // ریلود
        url.search = '';
        window.location.href = url.toString();
        return;
    }

    // Author picker: apply the choice on pick instead of making the reader
    // press "فیلتر" after it. Progressive only — with the script blocked the
    // radios still post with the form, which is why they are radios.
    const authorPicker = document.getElementById('blogAuthorPicker');
    if (authorPicker) {
        const form = authorPicker.closest('form');
        authorPicker.addEventListener('change', function (event) {
            if (event.target.type !== 'radio') return;
            authorPicker.open = false;
            if (form) form.requestSubmit ? form.requestSubmit() : form.submit();
        });

        // Click outside closes it; <details> has no such behaviour of its own.
        document.addEventListener('click', function (event) {
            if (authorPicker.open && !authorPicker.contains(event.target)) {
                authorPicker.open = false;
            }
        });
    }

});