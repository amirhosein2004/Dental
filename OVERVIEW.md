# 🦷 نمای کلی سیستم مدیریت کلینیک دندانپزشکی

## 📋 فهرست مطالب

- [معرفی پروژه](#معرفی-پروژه)
- [ویژگی‌های کلیدی](#ویژگی‌های-کلیدی)
- [معماری سیستم](#معماری-سیستم)
- [ماژول‌های اصلی](#ماژول‌های-اصلی)
- [تکنولوژی‌های استفاده شده](#تکنولوژی‌های-استفاده-شده)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [امنیت](#امنیت)
- [پشتیبانی](#پشتیبانی)

---

## 🏥 معرفی پروژه

سیستم مدیریت کلینیک دندانپزشکی **sbdental.ir** یک پلتفرم جامع و حرفه‌ای است که با استفاده از فریمورک Django طراحی و توسعه یافته است. این سیستم برای مدیریت کامل فعالیت‌های یک کلینیک دندانپزشکی از جمله مدیریت بیماران، نوبت‌دهی، خدمات، و محتوای وبسایت طراحی شده است.

### 🎯 اهداف پروژه

- **مدیریت یکپارچه**: ارائه یک سیستم یکپارچه برای مدیریت تمام جنبه‌های کلینیک
- **تجربه کاربری بهتر**: رابط کاربری ساده و کاربرپسند برای پزشکان و بیماران
- **امنیت بالا**: پیاده‌سازی بهترین استانداردهای امنیتی
- **مقیاس‌پذیری**: قابلیت توسعه و تطبیق با نیازهای مختلف
- **پشتیبانی از زبان فارسی**: پشتیبانی کامل از زبان فارسی و راست‌چین

---

## ✨ ویژگی‌های کلیدی

### 👥 مدیریت کاربران و احراز هویت
- **سیستم کاربری سفارشی**: مدل `CustomUser` با قابلیت‌های پیشرفته
- **احراز هویت دومرحله‌ای**: ورود با session و ایمیل + کد تأیید
- **رمزنگاری پیشرفته**: رمزنگاری session‌های ورودی کاربران
- **URL مخفی دکتر**: لینک اختصاصی و مخفی برای ورود پزشکان
- **بازیابی رمز عبور**: سیستم فراموشی رمز با لینک‌های زمان‌دار
- **محدودیت درخواست**: Rate limiting برای POST requests و admin panel
- **محافظت brute force**: Django Axes برای جلوگیری از حملات
- **Captcha و Honeypot**: محافظت در برابر ربات‌ها در فرم‌های ورود و تماس

### 🏥 مدیریت کلینیک
- **داشبورد اختصاصی دکتر**: پنل جداگانه با دسترسی به تغییر رمز، بلاگ‌ها و گالری‌ها
- **مدیریت اطلاعات کاربری**: امکان ویرایش پروفایل و اطلاعات شخصی دکتر
- **سیستم دسترسی متفاوت**: تفکیک کامل دسترسی‌های دکتران و کاربران عادی
- **مدیریت خدمات**: کاتالوگ کامل خدمات دندانپزشکی
- **گالری با فیلتر**: نمایش و فیلتر تصاویر بر اساس دسته‌بندی
- **مدیریت مطب**: تنظیمات مطب، ساعات کاری و اطلاعات تماس
- **خروج امن**: سیستم logout امن برای دکتران

### 📝 سیستم محتوا
- **وبلاگ با فیلتر**: انتشار مقالات با فیلتر بر اساس عنوان، نویسنده و دسته‌بندی
- **ویرایش توسط دکتر**: دکتران قابلیت ویرایش بلاگ‌ها و گالری‌های خود را دارند
- **ویرایشگر CKEditor**: CKEditor 5 با پشتیبانی کامل فارسی
- **URL با Slug**: استفاده از slug برای SEO بهتر و تجربه کاربری بهتر
- **سیستم دسته‌بندی**: تگ‌گذاری و دسته‌بندی پیشرفته محتوا

### 📞 ارتباط با مشتریان
- **فرم تماس هوشمند**: سیستم پیام‌رسانی با اعتبارسنجی کامل
- **فیلتر پیام‌ها**: فیلتر پیام‌های کاربران در بخش مدیریتی دکتر
- **پاک‌سازی خودکار**: حذف خودکار پیام‌های قدیمی با Celery Beat
- **ارسال ایمیل**: ارسال ایمیل‌های خودکار با Celery
- **محافظت کامل**: Captcha، Honeypot و Rate limiting

---

## 🏗️ معماری سیستم

### ساختار کلی

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  Django App     │────│  PostgreSQL     │
│   (Port 80)     │    │  (Port 8000)    │    │  Database       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Redis Cache    │    │  Celery Worker  │
                       │  (Port 6379)    │    │  Background     │
                       └─────────────────┘    └─────────────────┘
```

### الگوهای طراحی

- **MVT Pattern**: استفاده از الگوی Model-View-Template جنگو
- **Repository Pattern**: جداسازی منطق دسترسی به داده‌ها
- **Service Layer**: لایه سرویس برای منطق کسب‌وکار
- **Caching Strategy**: استراتژی کش‌گذاری چندلایه
- **Async Processing**: پردازش ناهمزمان با Celery

---

## 📦 ماژول‌های اصلی

### 🏠 Home App
- **صفحه اصلی**: نمایش اطلاعات کلی کلینیک
- **بنرها**: مدیریت بنرهای تبلیغاتی
- **نمایش خدمات**: معرفی خدمات اصلی
- **آخرین مقالات**: نمایش جدیدترین مطالب وبلاگ

```python
# نمونه View کلاس صفحه اصلی
class HomeView(View):
    def get(self, request):
        context = {
            'banners': Banner.objects.all()[:5],
            'doctors': Doctor.objects.all(),
            'services': Service.objects.all()[:2],
            'clinic': Clinic.objects.filter(is_primary=True).first(),
            'blogs': BlogPost.objects.all()[:3],
            'galleries': Gallery.objects.all()[:2],
        }
        return render(request, 'home/home.html', context)
```

### 👤 Accounts App
- **ثبت‌نام کاربران**: فرآیند ثبت‌نام با تأیید ایمیل
- **ورود/خروج**: سیستم احراز هویت
- **مدیریت پروفایل**: ویرایش اطلاعات شخصی
- **بازیابی رمز عبور**: سیستم OTP برای بازیابی

### 🏥 Dashboard App
- **پنل دکتر**: مدیریت اطلاعات پزشک
- **مدیریت نوبت‌ها**: برنامه‌ریزی و مدیریت قرارها
- **آمار و گزارش**: نمایش آمار عملکرد
- **مدیریت بیماران**: فهرست و اطلاعات بیماران

### 🛠️ Service App
- **کاتالوگ خدمات**: فهرست کامل خدمات دندانپزشکی
- **جزئیات خدمات**: توضیحات تفصیلی هر خدمت
- **قیمت‌گذاری**: مدیریت قیمت خدمات
- **دسته‌بندی**: تقسیم‌بندی خدمات به دسته‌ها

### 📝 Blog App
- **مدیریت مقالات**: نوشتن و ویرایش مطالب
- **دسته‌بندی**: تگ‌گذاری و دسته‌بندی مقالات
- **نظرات**: سیستم نظردهی کاربران
- **SEO**: بهینه‌سازی برای موتورهای جستجو

### 🖼️ Gallery App
- **آلبوم تصاویر**: مدیریت گالری‌های مختلف
- **نمونه کارها**: نمایش نتایج درمان‌ها
- **تصاویر قبل/بعد**: مقایسه نتایج درمان
- **بهینه‌سازی تصاویر**: فشرده‌سازی و بهینه‌سازی

### 📞 Contact App
- **فرم تماس**: دریافت پیام‌ها از کاربران
- **اطلاعات تماس**: نمایش آدرس و شماره تماس
- **نقشه**: نمایش موقعیت کلینیک
- **ساعات کاری**: اطلاعات زمان‌بندی

### ℹ️ About App
- **درباره کلینیک**: معرفی کلینیک و تیم پزشکی
- **تاریخچه**: سابقه فعالیت کلینیک
- **مأموریت و چشم‌انداز**: اهداف و ارزش‌های کلینیک
- **گواهینامه‌ها**: نمایش مجوزها و گواهی‌ها

### 💰 Pricing App
- **مدیریت قیمت**: مدیریت قیمت خدمات
- **قیمت خدمات**: عملیات CRUD بر روی قیمت ها

### 🔧 Core App
- **بخش‌های مدیریتی**: جدا کردن بخش‌های مدیریتی در اپ core
- **مدیریت دسته‌بندی‌ها**: سیستم کامل دسته‌بندی محتوا
- **مدیریت مطب‌ها**: تنظیمات مطب و ساعات کاری
- **مدیریت پیام‌ها**: سیستم مدیریت پیام‌های کاربران
- **مدیریت بنرها**: کنترل بنرهای نمایشی سایت
- **متادیتا**: اطلاعات SEO و بهینه‌سازی

### 👥 Users App
- **مدل کاربری سفارشی**: `CustomUser` model
- **پروفایل‌های کاربری**: اطلاعات تکمیلی کاربران
- **مدیریت دسترسی‌ها**: کنترل سطح دسترسی
- **تاریخچه فعالیت**: ردیابی عملکرد کاربران

### 🛠️ Utils App
- **Common Imports**: import کردن کل پکیج‌ها و موارد مورد نیاز در یک فایل
- **کش‌گذاری**: مدیریت cache ساده و کاربردی
- **ایمیل**: ارسال ایمیل‌های خودکار با Celery
- **فایل‌ها**: مدیریت آپلود و دانلود
- **کدنویسی مرتب**: جداسازی اپ‌ها و ساختار منظم
- **مستندات**: document و comment نویسی برای کدها

---

## 💻 تکنولوژی‌های استفاده شده

### Backend Framework
```python
# Django 5.1.7 - فریمورک اصلی
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Custom Apps
    'home', 'accounts', 'dashboard', 'service',
    'blog', 'gallery', 'contact', 'about',
    'core', 'users', 'pricing',
    # Third-party Apps
    'django_ckeditor_5', 'captcha', 'axes',
    'storages', 'debug_toolbar', 'compressor',
]
```

### Frontend Technologies
- **HTML5**: ساختار صفحات وب
- **CSS3**: طراحی و استایل‌دهی پیشرفته
- **JavaScript**: تعامل کاربری و AJAX requests
- **Bootstrap**: فریمورک CSS واکنش‌گرا
- **AJAX**: ارتباط با سرور بدون refresh صفحه
- **Template Modular**: ماژولار کردن template ها و static files

### Database & Caching
- **PostgreSQL 15**: پایگاه داده اصلی با بهینه‌سازی کامل queries
- **Redis**: سیستم کش ساده و کاربردی + صف پیام‌ها
- **Connection Pooling**: زنده نگه‌داشتن اتصال دیتابیس برای 10 دقیقه
- **Atomic Models**: اتمیک کردن مدل‌ها برای بهبود عملکرد

### Task Queue & Background Processing
```python
# Celery Configuration - ارسال ایمیل و پاک‌سازی خودکار
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# Celery Beat - پاک کردن خودکار پیام‌های کاربران
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-messages': {
        'task': 'contact.tasks.cleanup_old_messages',
        'schedule': crontab(hour=2, minute=0),  # هر روز ساعت 2 صبح
    },
}
```

### Security & Authentication
- **اعتبارسنجی کامل**: validation تمام فرم‌ها و مدل‌ها
- **تنظیمات امنیتی پیشرفته**: جداسازی محیط‌های تست، توسعه و تولید
- **Django Signals**: invalidate کردن cache و ایجاد دکتر هنگام ساخت کاربر
- **Custom User Model**: customize کردن users با قابلیت‌های اختصاصی
- **Rate Limiting**: محدودیت درخواست‌های POST و admin panel

### Frontend & UI
- **فرانت کاربردی**: پیاده‌سازی کامل با HTML, CSS, JavaScript
- **مینیفای فایل‌ها**: فشرده‌سازی static files و تصاویر برای deployment
- **CKEditor Integration**: افزودن CKEditor برای ویرایش محتوا
- **Persian/RTL Support**: پشتیبانی کامل از زبان فارسی
- **Responsive Design**: طراحی واکنش‌گرا و mobile-first

### DevOps & Deployment
```dockerfile
# Docker Configuration - داکرایز کردن کل پروژه
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Dental.wsgi:application"]
```

### Cloud Storage & Infrastructure
- **Liara Cloud**: ذخیره media files بر روی سرور ابری لیارا
- **Gunicorn**: وب سرور WSGI برای production
- **Nginx**: پروکسی سرور و serve کردن static files
- **Environment Variables**: فایل .env برای متغیرهای محیطی

---

## ⚙️ نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.11+
- PostgreSQL 15+
- Redis Server
- Git

### مراحل نصب

#### 1. دریافت کد منبع
```bash
git clone https://github.com/amirhosein2004/Dental.git
cd Dental
```

#### 2. ایجاد محیط مجازی
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

#### 4. تنظیمات محیطی
```bash
cp .env.example .env
# ویرایش فایل .env با تنظیمات مورد نیاز
```

#### 5. راه‌اندازی پایگاه داده
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

#### 6. جمع‌آوری فایل‌های استاتیک
```bash
python manage.py collectstatic
```

#### 7. اجرای سرور توسعه
```bash
python manage.py runserver
```

### راه‌اندازی با Docker

```bash
# ایجاد و اجرای کانتینرها
docker-compose up -d

# اجرای migration ها
docker-compose exec web python manage.py migrate

# ایجاد کاربر مدیر
docker-compose exec web python manage.py createsuperuser
```

---

## 🔒 امنیت

### تدابیر امنیتی پیاده‌سازی شده

#### 1. احراز هویت و مجوزدهی
- **Custom User Model**: مدل کاربری سفارشی با قابلیت‌های پیشرفته
- **Session Management**: مدیریت نشست‌های کاربری
- **Permission System**: سیستم دسترسی‌های سطح‌بندی شده

#### 2. محافظت در برابر حملات
```python
# Django Axes Configuration
AXES_FAILURE_LIMIT = 4
AXES_COOLOFF_TIME = 48
AXES_LOCK_OUT_AT_FAILURE = True
```

#### 3. رمزنگاری و امنیت داده‌ها
- **Password Hashing**: رمزنگاری رمزهای عبور با PBKDF2
- **CSRF Protection**: محافظت در برابر حملات CSRF
- **XSS Protection**: جلوگیری از حملات XSS

#### 4. تنظیمات امنیتی
```python
# Security Settings
SECURE_ADMIN_PANEL = os.getenv('SECURE_ADMIN_PANEL')
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = False  # در محیط تولید
ALLOWED_HOSTS = ['sbdental.ir', 'www.sbdental.ir']
```

#### 5. reCAPTCHA Integration
```python
# Google reCAPTCHA
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')
```

---

## 📊 نظارت و عملکرد

### سیستم کش‌گذاری
```python
# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# نمونه استفاده از کش
def get_cached_data(request):
    cache_key = f"home_data_{request.user.id}"
    cached_data = cache.get(cache_key)
    if not cached_data:
        cached_data = expensive_database_operation()
        cache.set(cache_key, cached_data, 3600)  # 1 hour
    return cached_data
```

### بهینه‌سازی پایگاه داده
- **Select Related**: کاهش تعداد کوئری‌ها
- **Prefetch Related**: بهینه‌سازی روابط many-to-many
- **Database Indexing**: ایندکس‌گذاری فیلدهای مهم
- **Query Optimization**: بهینه‌سازی کوئری‌های پیچیده
- **بهینه‌سازی سرعت**: بهبود عملکرد کلی سیستم و دیتابیس
- **Connection Persistence**: زنده نگه‌داشتن اتصال دیتابیس برای 10 دقیقه

---

## 🔧 تنظیمات پیشرفته

### متغیرهای محیطی
```env
# Django Core
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=sbdental.ir,www.sbdental.ir

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dental_clinic
DB_USER=dental_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1
REDIS_URL_CELERY=redis://127.0.0.1:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=drsbdentals@gmail.com
EMAIL_HOST_PASSWORD=app_password

# Security
RECAPTCHA_PUBLIC_KEY=your_public_key
RECAPTCHA_PRIVATE_KEY=your_private_key
OTP_SECRET_KEY=your_otp_secret
```

### تنظیمات CKEditor
```python
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'link',
            'bulletedList', 'numberedList', 'blockQuote',
            'imageUpload', 'undo', 'redo', 'fontColor'
        ],
        'language': 'fa',
        'height': '300px',
        'width': '100%',
    }
}
```

---

## 🚀 استقرار در محیط تولید

### دیپلوی بر روی لیارا
پروژه بر روی سرورهای ابری لیارا دیپلوی شده است:

```bash
# دیپلوی با لیارا CLI
liara deploy --app dental-clinic --port 8000

# تنظیمات محیطی در لیارا
liara env:set SECRET_KEY=your-secret-key
liara env:set DEBUG=False
liara env:set ALLOWED_HOSTS=sbdental.ir,www.sbdental.ir
```

### تنظیمات Nginx
```nginx
server {
    listen 80;
    server_name sbdental.ir www.sbdental.ir;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### تنظیمات Gunicorn
```bash
gunicorn --bind 0.0.0.0:8000 \
         --workers 4 \
         --timeout 120 \
         --max-requests 1000 \
         --preload \
         Dental.wsgi:application
```

### Docker Compose تولید
```yaml
version: '3.8'
services:
  web:
    build: .
    restart: always
    environment:
      - DJANGO_ENV=prod
    depends_on:
      - db
      - redis
    
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: dental_clinic
      POSTGRES_USER: dental_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:latest
    restart: always
  
  nginx:
    image: nginx:latest
    restart: always
    ports:
      - "80:80"
    depends_on:
      - web
```

---

## 🤝 مشارکت در پروژه

### راهنمای مشارکت

1. **Fork کردن پروژه**
2. **ایجاد شاخه جدید**: `git checkout -b feature/new-feature`
3. **Commit تغییرات**: `git commit -m 'Add new feature'`
4. **Push به شاخه**: `git push origin feature/new-feature`
5. **ایجاد Pull Request**

### استانداردهای کدنویسی
- پیروی از PEP 8
- استفاده از docstring برای توابع
- نوشتن تست برای قابلیت‌های جدید
- کامنت‌گذاری مناسب کد

### تست‌ها
```bash
# اجرای تمام تست‌ها
python manage.py test

# اجرای تست‌های یک اپ خاص
python manage.py test home

# اجرای تست با coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 📞 پشتیبانی و تماس

### اطلاعات تماس
- **وبسایت**: [sbdental.ir](https://sbdental.ir)
- **ایمیل پشتیبانی**: drsbdentals@gmail.com
- **مخزن گیت‌هاب**: [https://github.com/amirhosein2004/Dental](https://github.com/amirhosein2004/Dental.git)

### گزارش مشکلات
برای گزارش باگ‌ها یا درخواست قابلیت‌های جدید، لطفاً از بخش Issues گیت‌هاب استفاده کنید.

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای اطلاعات بیشتر فایل [LICENSE](LICENSE) را مطالعه کنید.

---

<div align="center">

**ساخته شده با ❤️ برای جامعه دندانپزشکی**

⭐ **اگر این پروژه برایتان مفید بود، ستاره دهید!** ⭐

</div>
