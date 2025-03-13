from .common_imports import ValidationError, FileExtensionValidator, URLValidator, MaxLengthValidator, MinLengthValidator, RegexValidator
from PIL import Image

def validate_image(value, max_size_mb=5, allowed_extensions=['jpg', 'jpeg', 'png']):
    """
    Validate an image for size, format, and actual content.

    Args:
        value: The image file to validate.
        max_size_mb: Maximum allowed size in megabytes (default: 5).
        allowed_extensions: List of allowed file extensions (default: ['jpg', 'jpeg', 'png']).
    
    Raises:
        ValidationError: If the image is invalid.
    """
    
    if not value:  # If the value is empty, return
        return

    # Check the size of the image
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"حجم تصویر باید کمتر از {max_size_mb} مگابایت باشد")
    
    # Check the file extension
    validator = FileExtensionValidator(
        allowed_extensions=allowed_extensions,
        message='فقط فایل‌هایی با پسوندهای jpg, jpeg, png مجاز هستند'
    )
    validator(value)
    
    # Check the actual content of the image
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
    Validate a URL with allowed schemes and maximum length.

    Args:
        value: The URL to validate.
        schemes: List of allowed schemes (default: ['http', 'https']).
    
    Raises:
        ValidationError: If the URL is invalid.
    """
    if not value:  # If the value is empty, return
        return

    URLValidator(schemes=schemes)(value)

def validate_text(value, min_length=10, max_length=500):
    """
    Validate text for allowed length and format.

    Args:
        value: The text to validate.
        min_length: Minimum allowed length (default: 10).
        max_length: Maximum allowed length (default: 500).
    
    Raises:
        ValidationError: If the text is invalid.
    """

    if not value:  # If the value is empty, return
        return
    
    # Clean the input by stripping whitespace
    value = value.strip()

    # Check the minimum length
    MinLengthValidator(min_length, message=f"متن باید حداقل {min_length} کاراکتر باشد")(value)
    
    # Check the maximum length
    MaxLengthValidator(max_length, message=f"متن نباید بیشتر از {max_length} کاراکتر باشد")(value)
    
    # Check the format with regex
    RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="متن فقط می‌تواند شامل حروف، اعداد و علائم نگارشی رایج باشد"
    )(value)

def validate_phone(value):
    """
    Validate a mobile phone number.

    Args:
        value: The phone number to validate.
    
    Raises:
        ValidationError: If the phone number is invalid.
    """

    if not value:  # If the value is empty, return
        return
    
    # Clean the input by stripping whitespace
    value = value.strip()
    
    RegexValidator(
        regex=r'^09[0-9]{9}$',
        message="شماره تلفن باید با 09 شروع شده و 11 رقم باشد"
    )(value)

def validate_hour(value, min_value=0, max_value=23):
    """
    Validate an hour for allowed range.

    Args:
        value: The hour to validate.
        min_value: Minimum allowed value (default: 0).
        max_value: Maximum allowed value (default: 23).
    
    Raises:
        ValidationError: If the hour is invalid.
    """
    if not value:  # If the value is empty, return
        return
    if not isinstance(value, int):
        raise ValidationError("ساعت باید یک عدد صحیح باشد")
    if value < min_value or value > max_value:
        raise ValidationError(f"ساعت باید بین {min_value} و {max_value} باشد")
    
def validate_title(value):
    """
    Validate a blog post title.

    Args:
        value: The title to validate.
    
    Raises:
        ValidationError: If the title is invalid.
    """

    if not value:  # If the value is empty, return
        return
    # Clean the input by stripping whitespace
    value = value.strip()

    MinLengthValidator(5, message="عنوان باید حداقل ۵ کاراکتر باشد")(value)
    RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\-\(\)]+$',
        message="عنوان فقط می‌تواند شامل حروف، اعداد، فاصله، خط تیره و پرانتز باشد"
    )(value)

def validate_slug(value):
    """
    Validate a blog post slug.

    Args:
        value: The slug to validate.
    
    Raises:
        ValidationError: If the slug is invalid.
    """

    if not value:  # If the value is empty, return
        return
    
    RegexValidator(
        regex=r'^[a-z0-9\-]+$',
        message="اسلاگ فقط می‌تواند شامل حروف کوچک، اعداد و خط تیره باشد"
    )(value)

def validate_content(value):
    """
    Validate blog post content.

    Args:
        value: The content to validate.
    
    Raises:
        ValidationError: If the content is invalid.
    """

    if not value:  # If the value is empty, return
        return
    
    # Clean the input by stripping whitespace
    value = value.strip()

    MinLengthValidator(50, message="محتوا باید حداقل ۵۰ کاراکتر باشد")(value)
    MaxLengthValidator(10000, message="محتوا نباید بیشتر از ۱۰۰۰۰ کاراکتر باشد")(value)
    RegexValidator(
        regex=r'^[a-zA-Z0-9\u0600-\u06FF\s\.,!?():;"\'\-]+$',
        message="محتوا فقط می‌تواند شامل حروف، اعداد، فاصله و علائم نگارشی رایج باشد"
    )(value)