# استفاده از تصویر رسمی پایتون
FROM python:3.11

# تنظیم متغیرهای محیطی
ENV PYTHONUNBUFFERED=1

# ایجاد دایرکتوری برای اپلیکیشن
WORKDIR /app

# کپی کردن فقط فایل requirements.txt
COPY requirements.txt /app/

# نصب وابستگی‌ها (در این مرحله فقط نصب پکیج‌ها)
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# کپی کردن فایل‌های پروژه
COPY . /app/

# باز کردن پورت مورد نیاز
EXPOSE 8000

# اجرای برنامه با Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Dental.wsgi:application"]
