document.addEventListener('DOMContentLoaded', function () {
    const logoutBtn = document.querySelector('#logoutBtn');
    const logoutForm = document.querySelector('#logoutForm');

    logoutForm.addEventListener('submit', function () {
        logoutBtn.disabled = true;
        logoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>در حال خروج...';
    });
});