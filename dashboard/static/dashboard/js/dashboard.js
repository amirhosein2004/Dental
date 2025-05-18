document.addEventListener("DOMContentLoaded", function() {
    // ---------- پیش‌نمایش تصویر (ساده‌شده) ----------
    function showImagePreview() {
        console.log('Initializing simple image preview');
        // مستقیم به عناصر دسترسی پیدا کنیم
        const fileInput = document.getElementById('id_image');
        const preview = document.getElementById('profile-preview');
        
        // بررسی دسترسی به عناصر
        if (!fileInput || !preview) {
            console.error('Required elements not found: fileInput=', fileInput, 'preview=', preview);
            return;
        }
        
        console.log('Adding direct change event');
        
        // اضافه کردن رویداد تغییر برای نمایش پیش‌نمایش
        fileInput.onchange = function() {
            console.log('File input changed. Files:', this.files);
            
            if (this.files && this.files[0]) {
                var reader = new FileReader();
                
                reader.onload = function(e) {
                    console.log('File read successfully');
                    preview.src = e.target.result;
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        };
        
        // اضافه کردن رویداد اینلاین
        fileInput.setAttribute('onchange', "console.log('Inline change event fired'); if(this.files && this.files[0]) { var reader = new FileReader(); reader.onload = function(e) { document.getElementById('profile-preview').src = e.target.result; }; reader.readAsDataURL(this.files[0]); }");
    }
    
    // اجرای تابع راه‌اندازی پیش‌نمایش عکس
    showImagePreview();

    // Function to handle profile section activation
    function activateProfileSection() {
        const profileSection = document.getElementById("profile-section");
        if (profileSection) {
            // Remove active class from all content sections
            document.querySelectorAll(".content-section").forEach(section => {
                section.classList.remove("active");
            });
            profileSection.classList.add("active");

            // Remove active class from all profile forms
            document.querySelectorAll(".profile-form").forEach(form => {
                form.classList.remove("active");
            });

            // Remove active class from all sub-menu links
            document.querySelectorAll(".sub-menu-link").forEach(link => {
                link.classList.remove("active");
            });

            // Activate the current section and its corresponding menu link
            const currentForm = document.querySelector(`.profile-form[data-section="${currentSection}"]`);
            const currentLink = document.querySelector(`.sub-menu-link[data-target="${currentSection}"]`);
            
            if (currentForm) currentForm.classList.add("active");
            if (currentLink) currentLink.classList.add("active");
        }
    }

    // Track current active section
    let currentSection = "account-info";

    // Handle main menu navigation
    const menuLinks = document.querySelectorAll(".menu-link");
    menuLinks.forEach(link => {
        link.addEventListener("click", function(e) {
            e.preventDefault();
            
            // Remove active class from all menu links
            menuLinks.forEach(link => link.classList.remove("active"));
            this.classList.add("active");

            const targetSection = this.getAttribute("data-target");
            
            if (targetSection === "profile-section") {
                activateProfileSection();
            } else {
                // Hide all content sections
                document.querySelectorAll(".content-section").forEach(section => {
                    section.classList.remove("active");
                });
                
                // Show target section
                const section = document.getElementById(targetSection);
                if (section) section.classList.add("active");
            }
        });
    });

    // Handle sub-menu navigation
    const subMenuLinks = document.querySelectorAll(".sub-menu-link");
    subMenuLinks.forEach(link => {
        link.addEventListener("click", function(e) {
            e.preventDefault();
            
            const targetSection = this.getAttribute("data-target");
            currentSection = targetSection;

            if (document.getElementById("profile-section").classList.contains("active")) {
                // Remove active class from all sub-menu links
                subMenuLinks.forEach(link => link.classList.remove("active"));
                this.classList.add("active");

                // Hide all sub-content sections
                const subSections = document.querySelectorAll(".sub-content-section");
                subSections.forEach(section => section.classList.remove("active"));

                // Show target sub-section
                const targetSubSection = document.querySelector(`#${targetSection}`);
                if (targetSubSection) targetSubSection.classList.add("active");
            }
        });
    });

    // Activate initial section if profile is active
    const activeMenuLink = document.querySelector(".menu-link.active");
    if (activeMenuLink && activeMenuLink.getAttribute("data-target") === "profile-section") {
        activateProfileSection();
    }

    // Handle profile form submission
    const profileForms = document.querySelectorAll(".profile-form");
    profileForms.forEach(form => {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const messageDiv = document.createElement("div");
            messageDiv.className = "form-message";
            this.appendChild(messageDiv);

            const url = this.getAttribute("data-url");
            console.log("Sending form data to:", url);
            
            // بررسی کنیم آیا این فرم شامل عکس جدید است یا خیر
            const hasNewImage = formData.get('image') && formData.get('image').size > 0;
            console.log('Form includes new image:', hasNewImage);
            
            // چک کردن فایل انتخاب شده
            if (hasNewImage) {
                const imageFile = formData.get('image');
                console.log('Uploading image:', imageFile.name, 'Size:', imageFile.size);
            }

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": formData.get("csrfmiddlewaretoken")
                },
                body: formData
            })
            .then(response => {
                console.log("Response Status:", response.status);
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`HTTP Error ${response.status}: ${text}`);
                    });
                }
                return response.json().catch(err => {  // اگر پاسخ JSON نبود
                    console.log('Response is not JSON, returning text');
                    return response.text().then(text => ({ message: 'تغییرات با موفقیت ذخیره شد!' }));
                });
            })
            .then(data => {
                console.log('Form submission successful, data:', data);
                messageDiv.innerHTML = `<p style="color: green;">${data.message || 'تغییرات با موفقیت ذخیره شد!'}</p>`;
                
                // اگر عکس جدیدی آپلود شده بود و پاسخ آدرس عکس را داشت، عکس پروفایل را به‌روز کنیم
                if (data.image_url && hasNewImage) {
                    console.log('Updating profile image with server URL:', data.image_url);
                    const profilePreview = document.getElementById('profile-preview');
                    if (profilePreview) {
                        profilePreview.src = data.image_url + '?t=' + new Date().getTime();
                        console.log('Profile image updated with server URL');
                    }
                }
                
                setTimeout(() => messageDiv.remove(), 3000);
            })
            .catch(error => {
                console.error("Error Details:", error);
                messageDiv.innerHTML = `<p style="color: red;">خطا: ${error.message}</p>`;
                setTimeout(() => messageDiv.remove(), 5000);
            });
        });
    });

    // Handle password form submission
    const passwordForm = document.getElementById("password-form");
    if (passwordForm) {
        passwordForm.addEventListener("submit", function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const messagesDiv = document.getElementById("password-messages");
            messagesDiv.innerHTML = "";

            const url = this.getAttribute("data-url");
            console.log("Sending request to:", url);

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": formData.get("csrfmiddlewaretoken")
                },
                body: formData
            })
            .then(response => {
                console.log("Response Status:", response.status);
                if (response.redirected) {
                    messagesDiv.innerHTML = "<p style=\"color: green;\">رمز عبور با موفقیت تغییر کرد</p>";
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
                    const doc = parser.parseFromString(html, "text/html");
                    const errorList = doc.querySelectorAll(".errorlist");
                    
                    if (errorList.length > 0) {
                        let errorHtml = "<ul style=\"color: red;\">";
                        errorList.forEach(list => {
                            list.querySelectorAll("li").forEach(item => {
                                errorHtml += `<li>${item.textContent}</li>`;
                            });
                        });
                        errorHtml += "</ul>";
                        messagesDiv.innerHTML = errorHtml;
                    }
                }
            })
            .catch(error => {
                console.error("Error Details:", error);
                messagesDiv.innerHTML = `<p style="color: red;">خطا: ${error.message}</p>`;
            });
        });
    }

    // Handle delete confirmation modal
    const deleteButtons = document.querySelectorAll(".delete-btn");
    const deleteForm = document.getElementById("deleteForm");
    const deleteMessage = document.getElementById("deleteMessage");

    deleteButtons.forEach(button => {
        button.addEventListener("click", function() {
            const url = this.getAttribute("data-url");
            const title = this.getAttribute("data-title");
            deleteMessage.textContent = `آیا مطمئن هستید که می‌خواهید "${title}" را حذف کنید؟`;
            deleteForm.action = url;
        });
    });

    // Handle sidebar toggle
    const sidebar = document.querySelector(".sidebar");
    const sidebarToggle = document.querySelector(".sidebar-toggle");

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", function() {
            sidebar.classList.toggle("active");
        });

        // Close sidebar when clicking outside
        document.addEventListener("click", function(e) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove("active");
            }
        });
    }

    // Handle password visibility toggle
    const togglePasswordButtons = document.querySelectorAll(".toggle-password");
    togglePasswordButtons.forEach(button => {
        button.addEventListener("click", function() {
            const targetId = this.getAttribute("data-target");
            const passwordInput = document.getElementById(targetId);
            
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                this.classList.remove("fa-eye");
                this.classList.add("fa-eye-slash");
            } else {
                passwordInput.type = "password";
                this.classList.remove("fa-eye-slash");
                this.classList.add("fa-eye");
            }
        });
    });
});