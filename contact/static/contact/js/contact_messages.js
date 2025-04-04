
document.addEventListener('DOMContentLoaded', function() {
    const markAllForm = document.getElementById('markAllForm');
    if (markAllForm) {
        markAllForm.addEventListener('submit', function(event) {
            event.preventDefault(); // جلوگیری از رفتار پیش‌فرض فرم

            const confirmModal = new bootstrap.Modal(document.getElementById('confirmMarkAllModal'));
            confirmModal.show();

            document.getElementById('confirmMarkAllBtn').onclick = function() {
                fetch(markAllForm.action, {
                    method: 'POST',
                    body: new FormData(markAllForm),
                    headers: {
                        'X-CSRFToken': markAllForm.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                }).then(response => {
                    if (response.ok) {
                        confirmModal.hide();
                        updateAllMessagesStatus();
                        const successModal = new bootstrap.Modal(document.getElementById('markAllModal'));
                        successModal.show();
                    } else {
                        console.error('خطا در علامت‌گذاری همه پیام‌ها');
                    }
                }).catch(error => {
                    console.error('خطا:', error);
                });
            };
        });
    }

    // مدیریت فرم‌های علامت‌گذاری تک پیام
    document.querySelectorAll('form[action*="/mark_as_read/"]').forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
                }
            }).then(response => {
                if (response.ok) {
                    updateMessageStatus(form.closest('tr'));
                }
            });
        });
    });

    // به‌روزرسانی وضعیت همه پیام‌ها در رابط کاربری
    function updateAllMessagesStatus() {
        document.querySelectorAll('tbody tr').forEach(row => {
            row.classList.remove('table-warning');
            const badge = row.querySelector('.badge');
            badge.classList.remove('bg-danger');
            badge.classList.add('bg-success');
            badge.innerHTML = '<i class="fas fa-check me-2"></i>خوانده‌شده';
            
            const actionCell = row.querySelector('td:last-child');
            const markForm = actionCell.querySelector('form'); // فرم علامت‌گذاری
            if (markForm) {
                // فقط فرم را حذف کنید و دکمه مشاهده را نگه دارید
                markForm.remove();
            }
            // اگر فرم وجود نداشته باشد، یعنی پیام قبلاً خوانده‌شده است و نیازی به تغییر نیست
        });
    }
    // به‌روزرسانی وضعیت یک پیام در رابط کاربری
    function updateMessageStatus(row) {
        row.classList.remove('table-warning');
        const badge = row.querySelector('.badge');
        badge.classList.remove('bg-danger');
        badge.classList.add('bg-success');
        badge.innerHTML = '<i class="fas fa-check me-2"></i>خوانده‌شده';
        
        const actionCell = row.querySelector('td:last-child');
        actionCell.innerHTML = '<span class="text-muted small d-block">خوانده‌شده</span>';
    }
});