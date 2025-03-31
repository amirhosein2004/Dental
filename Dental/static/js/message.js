// اسکریپت برای مدیریت پیام‌ها
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.message');
    
    messages.forEach(message => {
        // بستن پیام با کلیک روی دکمه
        const closeBtn = message.querySelector('.message-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                message.classList.add('hide');
                setTimeout(() => message.remove(), 300);
            });
        }
        
        // بستن خودکار پیام‌ها پس از 5 ثانیه
        setTimeout(() => {
            message.classList.add('hide');
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});