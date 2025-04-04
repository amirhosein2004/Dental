# استفاده از تصویر رسمی پایتون
FROM python:3.11

# تنظیم متغیرهای محیطی
ENV PYTHONUNBUFFERED=1

# ایجاد دایرکتوری برای اپلیکیشن
WORKDIR /app

# کپی کردن فایل‌های پروژه
COPY . /app/

# نصب وابستگی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# جمع‌آوری فایل‌های استاتیک
RUN python manage.py collectstatic --noinput

# باز کردن پورت مورد نیاز
EXPOSE 8000

# اجرای برنامه با Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Dental.wsgi:application"]
