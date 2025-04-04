// core/js/workinghour.js
document.addEventListener('DOMContentLoaded', function() {
    // مدیریت دکمه ویرایش
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            document.getElementById(`row-${id}`).style.display = 'none';
            document.getElementById(`edit-form-${id}`).style.display = 'table-row';
        });
    });

    // مدیریت دکمه لغو
    document.querySelectorAll('.cancel-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            document.getElementById(`row-${id}`).style.display = 'table-row';
            document.getElementById(`edit-form-${id}`).style.display = 'none';
        });
    });
});