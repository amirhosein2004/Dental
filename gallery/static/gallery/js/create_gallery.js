document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.querySelector('input[type="file"]');
    const previewContainer = document.getElementById('image-preview');

    if (imageInput && previewContainer) {
        imageInput.addEventListener('change', function(event) {
            previewContainer.innerHTML = ''; // پاک کردن پیش‌نمایش‌های قبلی

            const files = event.target.files;
            const fileList = Array.from(files); // تبدیل به آرایه برای مدیریت بهتر

            fileList.forEach((file, index) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const imgContainer = document.createElement('div');
                    imgContainer.className = 'position-relative d-inline-block m-2';

                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'img-thumbnail';
                    img.style.maxWidth = '150px';
                    img.style.maxHeight = '150px';
                    img.alt = 'پیش‌نمایش تصویر';

                    // دکمه ضربدر
                    const deleteButton = document.createElement('button');
                    deleteButton.innerHTML = '&times;'; // علامت ضربدر
                    deleteButton.className = 'btn btn-danger btn-sm position-absolute top-0 end-0';
                    deleteButton.style.lineHeight = '1';
                    deleteButton.style.padding = '2px 6px';
                    deleteButton.title = 'حذف تصویر';
                    deleteButton.onclick = function() {
                        // حذف تصویر از پیش‌نمایش
                        imgContainer.remove();

                        // به‌روزرسانی فایل‌ها در input
                        const newFileList = Array.from(imageInput.files).filter((_, i) => i !== index);
                        const dataTransfer = new DataTransfer();
                        newFileList.forEach(f => dataTransfer.items.add(f));
                        imageInput.files = dataTransfer.files;
                    };

                    imgContainer.appendChild(img);
                    imgContainer.appendChild(deleteButton);
                    previewContainer.appendChild(imgContainer);
                };
                reader.readAsDataURL(file);
            });
        });
    }
});