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

});