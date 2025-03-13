from .common_imports import ValidationError, FileExtensionValidator, URLValidator, MaxLengthValidator, MinLengthValidator, RegexValidator
from PIL import Image

def validate_image(value, max_size_mb=5, allowed_extensions=['jpg', 'jpeg', 'png']):
    """اعتبارسنجی تصویر برای حجم، فرمت و محتوای واقعی."""
    
    if not value:  # اگه خالی باشه، رد می‌شه
        return

    # چک کردن حجم
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"حجم تصویر باید کمتر از {max_size_mb} مگابایت باشد")
    
    # چک کردن فرمت
    validator = FileExtensionValidator(
        allowed_extensions=allowed_extensions,
        message='فقط فایل‌هایی با پسوندهای jpg, jpeg, png مجاز هستند'
    )
    validator(value)
    
    # چک کردن محتوای واقعی
    try:
        img = Image.open(value)
        img.verify()
        width, height = img.size
        if width > 5000 or height > 5000:
            raise ValidationError("ابعاد تصویر نباید بیشتر از ۵۰۰۰x۵۰۰۰ پیکسل باشد")
    except Exception:
        raise ValidationError("فایل ارسال‌شده یک تصویر معتبر نیست")
    
def validate_url(value, schemes=['http', 'https']):
    """
    اعتبارسنجی URL با طرح‌های مجاز و حداکثر طول.

    Args:
        value: مقدار URL برای اعتبارسنجی
        schemes: لیست طرح‌های مجاز (پیش‌فرض: ['http', 'https'])
    Raises:
        ValidationError: اگر URL نامعتبر باشد
    """
    if not value:  # اگه خالی باشه، رد می‌شه
        return

    URLValidator(schemes=schemes)(value)

def validate_text(value, min_length=10, max_length=500):
    """
    اعتبارسنجی متن برای طول و فرمت مجاز.

    Args:
        value: مقدار متن برای اعتبارسنجی
        min_length: حداقل طول مجاز (پیش‌فرض: ۱۰)
        max_length: حداکثر طول مجاز (پیش‌فرض: ۵۰۰)
    Raises:
        ValidationError: اگر متن نامعتبر باشد
    """

    if not value:  # اگه خالی باشه، رد می‌شه
        return
    
    # تمیز کردن ورودی با strip
    value = value.strip()

    # چک حداقل طول
    MinLengthValidator(min_length, message=f"متن باید حداقل {min_length} کاراکتر باشد")(value)
    
    # چک حداکثر طول
    MaxLengthValidator(max_length, message=f"متن نباید بیشتر از {max_length} کاراکتر باشد")(value)
    
    # چک فرمت با regex
    RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="متن فقط می‌تواند شامل حروف، اعداد و علائم نگارشی رایج باشد"
    )(value)

def validate_phone(value):
    """
    اعتبارسنجی شماره تلفن موبایل.

    Args:
        value: مقدار شماره تلفن برای اعتبارسنجی
    Raises:
        ValidationError: اگر شماره تلفن نامعتبر باشد
    """

    if not value:  # اگه خالی باشه، رد می‌شه
        return
    
    # تمیز کردن ورودی با strip
    value = value.strip()
    
    RegexValidator(
        regex=r'^09[0-9]{9}$',
        message="شماره تلفن باید با 09 شروع شده و 11 رقم باشد"
    )(value)

def validate_hour(value, min_value=0, max_value=23):
    """
    اعتبارسنجی ساعت برای محدوده مجاز.

    Args:
        value: مقدار ساعت برای اعتبارسنجی
        min_value: حداقل مقدار مجاز (پیش‌فرض: ۰)
        max_value: حداکثر مقدار مجاز (پیش‌فرض: ۲۳)
    Raises:
        ValidationError: اگر مقدار نامعتبر باشد
    """
    if not value:  # اگه خالی باشه، رد می‌شه
        return
    if not isinstance(value, int):
        raise ValidationError("ساعت باید یک عدد صحیح باشد")
    if value < min_value or value > max_value:
        raise ValidationError(f"ساعت باید بین {min_value} و {max_value} باشد")
    
def validate_title(value):
    """اعتبارسنجی عنوان پست وبلاگ."""

    if not value:  # اگه خالی باشه، رد می‌شه
        return
    # تمیز کردن ورودی با strip
    value = value.strip()

    MinLengthValidator(5, message="عنوان باید حداقل ۵ کاراکتر باشد")(value)
    RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\-\(\)]+$',
        message="عنوان فقط می‌تواند شامل حروف، اعداد، فاصله، خط تیره و پرانتز باشد"
    )(value)

def validate_slug(value):
    """اعتبارسنجی اسلاگ پست وبلاگ."""

    if not value:  # اگه خالی باشه، رد می‌شه
        return
    
    RegexValidator(
        regex=r'^[a-z0-9\-]+$',
        message="اسلاگ فقط می‌تواند شامل حروف کوچک، اعداد و خط تیره باشد"
    )(value)

def validate_content(value):
    """اعتبارسنجی محتوای پست وبلاگ."""

    if not value:  # اگه خالی باشه، رد می‌شه
        return
    
    # تمیز کردن ورودی با strip
    value = value.strip()

    MinLengthValidator(50, message="محتوا باید حداقل ۵۰ کاراکتر باشد")(value)
    MaxLengthValidator(10000, message="محتوا نباید بیشتر از ۱۰۰۰۰ کاراکتر باشد")(value)
    RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="محتوا فقط می‌تواند شامل حروف، اعداد، فاصله و علائم نگارشی رایج باشد"
    )(value)