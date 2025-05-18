document.querySelector('input[name="image"]').onchange = function (event) {
    const [file] = event.target.files;
    const previewContainer = document.getElementById('image-preview-container');
    const previewImage = document.getElementById('image-preview');
    const currentImageContainer = document.getElementById('current-image-container');

    if (file) {
        previewImage.src = URL.createObjectURL(file);
        previewContainer.style.display = 'block';
        if (currentImageContainer) {
            currentImageContainer.style.display = 'none';
        }
    } else {
        previewImage.src = '#';
        previewContainer.style.display = 'none';
         if (currentImageContainer) {
            currentImageContainer.style.display = 'block';
        }
    }
}; 