document.addEventListener("DOMContentLoaded", function () {
  // متغیر برای ذخیره آخرین زیربخش فعال
  let lastActiveSubSection = 'account-info';

  // تابع برای فعال کردن بخش پروفایل و زیربخش ذخیره‌شده
  function activateProfileSection() {
    const profileSection = document.getElementById('profile-section');
    if (profileSection) {
      document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
      profileSection.classList.add('active');

      document.querySelectorAll('.profile-form').forEach(form => form.classList.remove('active'));
      document.querySelectorAll('.sub-menu-link').forEach(link => link.classList.remove('active'));

      const targetForm = document.querySelector(`.profile-form[data-section="${lastActiveSubSection}"]`);
      const targetLink = document.querySelector(`.sub-menu-link[data-target="${lastActiveSubSection}"]`);
      if (targetForm) targetForm.classList.add('active');
      if (targetLink) targetLink.classList.add('active');
    }
  }

  // مدیریت منوهای اصلی
  const menuLinks = document.querySelectorAll('.menu-link');
  menuLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      menuLinks.forEach(l => l.classList.remove('active'));
      this.classList.add('active');

      const targetId = this.getAttribute('data-target');
      if (targetId === 'profile-section') {
        activateProfileSection();
      } else {
        document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
        const targetSection = document.getElementById(targetId);
        if (targetSection) targetSection.classList.add('active');
      }
    });
  });

  // مدیریت زیرمنوهای پروفایل
  const subMenuLinks = document.querySelectorAll('.sub-menu-link');
  subMenuLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('data-target');
      lastActiveSubSection = targetId;

      if (document.getElementById('profile-section').classList.contains('active')) {
        // مدیریت فعال بودن لینک‌های زیرمنو
        subMenuLinks.forEach(l => l.classList.remove('active'));
        this.classList.add('active');

        // مدیریت نمایش بخش‌های داخل فرم
        const subSections = document.querySelectorAll('.sub-content-section');
        subSections.forEach(section => section.classList.remove('active'));

        const targetSection = document.querySelector(`#${targetId}`);
        if (targetSection) targetSection.classList.add('active');
      }
    });
  });

  // فعال‌سازی اولیه بخش پروفایل
  const activeMenuLink = document.querySelector('.menu-link.active');
  if (activeMenuLink && activeMenuLink.getAttribute('data-target') === 'profile-section') {
    activateProfileSection();
  }

  // ارسال فرم‌های پروفایل با آژاکس
  const profileForms = document.querySelectorAll('.profile-form');
  profileForms.forEach(form => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const messageContainer = document.createElement('div');
      messageContainer.className = 'form-message';
      this.appendChild(messageContainer);

      const url = this.getAttribute('data-url'); // گرفتن URL از ویژگی data-url
      console.log("Sending request to:", url); // برای عیب‌یابی

      fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": formData.get('csrfmiddlewaretoken') },
        body: formData
      })
      .then(response => {
        console.log("Response Status:", response.status);
        if (!response.ok) {
          return response.text().then(text => {
            throw new Error(`HTTP Error ${response.status}: ${text}`);
          });
        }
        return response.text();
      })
      .then(data => {
        messageContainer.innerHTML = '<p style="color: green;">تغییرات با موفقیت ذخیره شد!</p>';
        setTimeout(() => messageContainer.remove(), 3000);
      })
      .catch(error => {
        console.error("Error Details:", error);
        messageContainer.innerHTML = `<p style="color: red;">خطا: ${error.message}</p>`;
        setTimeout(() => messageContainer.remove(), 5000);
      });
    });
  });

  // ارسال فرم تغییر رمز عبور با آژاکس
  const passwordForm = document.getElementById('password-form');
  if (passwordForm) {
    passwordForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const messagesDiv = document.getElementById('password-messages');
      messagesDiv.innerHTML = '';

      const url = this.getAttribute('data-url'); // گرفتن URL از ویژگی data-url
      console.log("Sending request to:", url); // برای عیب‌یابی

      fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": formData.get('csrfmiddlewaretoken') },
        body: formData
      })
      .then(response => {
        console.log("Response Status:", response.status);
        if (response.redirected) {
          messagesDiv.innerHTML = '<p style="color: green;">رمز عبور با موفقیت تغییر کرد</p>';
          this.reset();
          return null;
        }
        if (!response.ok) {
          return response.text().then(text => {
            throw new Error(`HTTP Error ${response.status}: ${text}`);
          });
        }
        return response.text();
      })
      .then(html => {
        if (html) {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          const errorLists = doc.querySelectorAll('.errorlist');
          if (errorLists.length > 0) {
            let errorMessages = '<ul style="color: red;">';
            errorLists.forEach(list => {
              list.querySelectorAll('li').forEach(item => {
                errorMessages += `<li>${item.textContent}</li>`;
              });
            });
            errorMessages += '</ul>';
            messagesDiv.innerHTML = errorMessages;
          }
        }
      })
      .catch(error => {
        console.error("Error Details:", error);
        messagesDiv.innerHTML = `<p style="color: red;">خطا: ${error.message}</p>`;
      });
    });
  }

  // مدیریت دکمه‌های حذف و مودال
  const deleteButtons = document.querySelectorAll('.delete-btn');
  const deleteForm = document.getElementById('deleteForm');
  const deleteMessage = document.getElementById('deleteMessage');

  deleteButtons.forEach(button => {
    button.addEventListener('click', function () {
      const url = this.getAttribute('data-url');
      const title = this.getAttribute('data-title');
      deleteMessage.textContent = `آیا مطمئن هستید که می‌خواهید "${title}" را حذف کنید؟`;
      deleteForm.action = url;
    });
  });

  // مدیریت سایدبار
  const sidebar = document.querySelector('.sidebar');
  const toggleButton = document.querySelector('.sidebar-toggle');

  if (toggleButton && sidebar) {
    toggleButton.addEventListener('click', function () {
      sidebar.classList.toggle('active');
    });

    document.addEventListener('click', function (event) {
      if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
        sidebar.classList.remove('active');
      }
    });
  }

  //show password
  const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const passwordField = document.getElementById(targetId);
            
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            } else {
                passwordField.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            }
        });
    });
}); 