// static/core/js/category.js
document.addEventListener('DOMContentLoaded', function() {
    const categoryList = document.getElementById('category-list');

    // ویرایش دسته‌بندی
    categoryList.addEventListener('click', function(e) {
        if (e.target.classList.contains('edit-btn')) {
            const item = e.target.closest('.category-item');
            const editForm = item.querySelector('.edit-form');
            const editInput = editForm.querySelector('.edit-input');
            const nameSpan = item.querySelector('.category-name');

            // نمایش فرم ویرایش
            nameSpan.style.display = 'none';
            editForm.style.display = 'inline';
            editInput.focus();

            // ارسال تغییرات هنگام خروج از فوکوس (کلیک در جای دیگر)
            editInput.addEventListener('blur', function handler() {
                const formData = new FormData(editForm);
                fetch(editForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        nameSpan.textContent = data.category_name;
                        editInput.value = data.category_name;
                        nameSpan.style.display = 'inline';
                        editForm.style.display = 'none';
                    } else {
                        // در صورت خطا، فرم را ببندید یا پیام خطا نمایش دهید
                        nameSpan.style.display = 'inline';
                        editForm.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('خطا: ', error);
                    nameSpan.style.display = 'inline';
                    editForm.style.display = 'none';
                });

                // حذف رویداد پس از اتمام
                editInput.removeEventListener('blur', handler);
            });
        }
    });
});