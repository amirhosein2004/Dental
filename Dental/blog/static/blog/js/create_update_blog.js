document.addEventListener('DOMContentLoaded', () => {


    //  پیش‌نمایش تصویر
    const imageInput = document.querySelector('#id_image');
    const imagePreview = document.querySelector('#imagePreview');
    const imagePreviewImg = document.querySelector('#imagePreviewImg');
    const currentImage = document.querySelector('#currentImage');

    if (imageInput) {
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    imagePreviewImg.src = event.target.result;
                    imagePreview.style.display = 'block';
                    if (currentImage) currentImage.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    //  اعتبارسنجی فرم
    const form = document.querySelector('#blogForm');
    form.addEventListener('submit', (e) => {
        let isValid = true;

        // بررسی عنوان
        const titleInput = document.querySelector('#id_title');
        if (!titleInput.value.trim()) {
            isValid = false;
            titleInput.classList.add('is-invalid');
        } else {
            titleInput.classList.remove('is-invalid');
        }

        // بررسی دسته‌بندی‌ها (حداقل یک مورد)
        const categoriesChecked = document.querySelectorAll('.category-item input[type="checkbox"]:checked').length;
        const categoryContainer = document.querySelector('.category-list');
        if (categoriesChecked === 0) {
            isValid = false;
            categoryContainer.insertAdjacentHTML('afterend', '<div class="invalid-feedback d-block">لطفاً حداقل یک دسته‌بندی انتخاب کنید.</div>');
        } else {
            const existingFeedback = categoryContainer.nextElementSibling;
            if (existingFeedback && existingFeedback.classList.contains('invalid-feedback')) {
                existingFeedback.remove();
            }
        }

        // بررسی محتوا (اگر CKEditor استفاده می‌شود)
        const contentEditor = window.CKEDITOR ? CKEDITOR.instances['id_content'] : null;
        if (contentEditor && !contentEditor.getData().trim()) {
            isValid = false;
            contentEditor.container.addClass('is-invalid');
            contentEditor.container.find('.cke_bottom').after('<div class="invalid-feedback d-block">محتوا نمی‌تواند خالی باشد.</div>');
        } else if (contentEditor) {
            contentEditor.container.removeClass('is-invalid');
            const existingFeedback = contentEditor.container.find('.invalid-feedback');
            if (existingFeedback) existingFeedback.remove();
        }

        if (!isValid) {
            e.preventDefault(); // جلوگیری از ارسال فرم در صورت خطا
        }
    });

    //  حذف خطا هنگام تایپ
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            input.classList.remove('is-invalid');
        });
    });
});