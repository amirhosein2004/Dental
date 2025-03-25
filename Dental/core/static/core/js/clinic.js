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