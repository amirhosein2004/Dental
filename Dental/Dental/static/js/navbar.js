// // تغییر استایل نوار ناوبری موقع اسکرول
// window.addEventListener('scroll', () => {
//     const navbar = document.querySelector('.navbar');
//     if (window.scrollY > 50) {
//         navbar.classList.add('scrolled');
//     } else {
//         navbar.classList.remove('scrolled');
//     }
// });

// // انیمیشن نرم برای باز شدن منو در موبایل
// const navbarToggler = document.querySelector('.navbar-toggler');
// const navbarCollapse = document.querySelector('.navbar-collapse');

// navbarToggler.addEventListener('click', () => {
//     if (!navbarCollapse.classList.contains('show')) {
//         navbarCollapse.style.height = '0';
//         navbarCollapse.classList.add('show');
//         setTimeout(() => {
//             navbarCollapse.style.height = navbarCollapse.scrollHeight + 'px';
//         }, 10);
//     } else {
//         navbarCollapse.style.height = navbarCollapse.scrollHeight + 'px';
//         setTimeout(() => {
//             navbarCollapse.style.height = '0';
//         }, 10);
//         setTimeout(() => {
//             navbarCollapse.classList.remove('show');
//         }, 300);
//     }
// });