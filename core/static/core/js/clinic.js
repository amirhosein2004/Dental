function toggleEdit(clinicId) {
    const clinicCard = document.getElementById(`clinic-${clinicId}`);
    const displayMode = clinicCard.querySelector('.display-mode');
    const editMode = clinicCard.querySelector('.edit-mode');
    
    if (displayMode.style.display === 'none') {
        displayMode.style.display = 'block';
        editMode.style.display = 'none';
    } else {
        displayMode.style.display = 'none';
        editMode.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // برای هر فرم ویرایش کلینیک
    document.querySelectorAll('.clinic-card .edit-mode').forEach(function(editMode) {
        const imageInput = editMode.querySelector('input[type="file"][name="image"]');
        const previewImg = editMode.querySelector('img[id^="clinic-image-preview-"]');
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
});