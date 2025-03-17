from .common_imports import ValidationError, FileExtensionValidator, MaxLengthValidator, MinLengthValidator, RegexValidator
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
    except Exception:
        raise ValidationError("فایل ارسال‌شده یک تصویر معتبر نیست")

def validate_length(value, min_length=10, max_length=500):
    """
    Validate text

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
    MinLengthValidator(min_length, message=f"محتوا باید حداقل {min_length} کاراکتر باشد")(value)
    
    # Check the maximum length
    MaxLengthValidator(max_length, message=f"محتوا نباید بیشتر از {max_length} کاراکتر باشد")(value)

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