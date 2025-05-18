// نمایش پیش‌نمایش تصویر آپلود شده کلینیک

document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.querySelector('input[type="file"][name$="image"]');
    const previewImg = document.getElementById('clinic-image-preview');
    if (imageInput && previewImg) {
        imageInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    previewImg.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                previewImg.src = '#';
                previewImg.style.display = 'none';
            }
        });
    }
}); 