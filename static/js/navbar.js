document.addEventListener('DOMContentLoaded', () => {
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelectorAll('.nav-link');
  
    // افکت اسکرول برای navbar
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        navbar.style.padding = '0.5rem 0';
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
      } else {
        navbar.style.padding = '1rem 0';
        navbar.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
      }
    });
  
    // انیمیشن کلیک روی لینک‌ها
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        link.style.transform = 'scale(0.95)';
        setTimeout(() => {
          link.style.transform = 'scale(1)';
        }, 100);
      });
    });
  });