document.addEventListener('DOMContentLoaded', () => {
    // پیش‌نمایش تصویر قبل از آپلود
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const preview = document.createElement('img');
                preview.src = URL.createObjectURL(file);
                preview.className = 'banner-image mt-2';
                preview.style.maxWidth = '150px';

                const previousPreview = fileInput.nextElementSibling;
                if (previousPreview && previousPreview.tagName === 'IMG') {
                    previousPreview.remove();
                }

                fileInput.parentNode.appendChild(preview);
            }
        });
    }

    // تأیید برای فرم‌های حذف
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const bannerTitle = form.closest('tr').querySelector('td:nth-child(2)').textContent;
            if (!confirm(`آیا از حذف «${bannerTitle}» مطمئن هستید؟`)) {
                e.preventDefault();
            }
        });
    });

    // پیش‌نمایش تصویر بزرگ در مدال
    const modal = document.getElementById('imagePreviewModal');
    const modalImg = document.getElementById('previewImage');
    const closeModal = document.querySelector('.close-modal');
    const bannerImages = document.querySelectorAll('.banner-image');

    bannerImages.forEach(image => {
        image.addEventListener('click', () => {
            modal.style.display = 'flex';
            modalImg.src = image.getAttribute('data-large-src');
        });
    });

    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});