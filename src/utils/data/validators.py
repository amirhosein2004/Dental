from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxLengthValidator,
    MinLengthValidator,
    RegexValidator,
)
from PIL import Image

DEFAULT_IMAGE_EXTENSIONS = ('jpg', 'jpeg', 'png')


def validate_image(value, max_size_mb=5, allowed_extensions=None):
    """
    Validate an image for size, format, and actual content.

    Args:
        value: The image file to validate.
        max_size_mb: Maximum allowed size in megabytes (default: 5).
        allowed_extensions: Iterable of allowed file extensions; defaults to jpg/jpeg/png.

    Raises:
        ValidationError: If the image is invalid.
    """
    if not value:
        return

    extensions = list(allowed_extensions) if allowed_extensions else list(DEFAULT_IMAGE_EXTENSIONS)

    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"حجم تصویر باید کمتر از {max_size_mb} مگابایت باشد")

    FileExtensionValidator(
        allowed_extensions=extensions,
        message=f"فقط فایل‌هایی با پسوندهای {', '.join(extensions)} مجاز هستند",
    )(value)

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

def validate_rich_length(value, min_length=10, max_length=1500):
    """
    Length check for a field the staff edits in a rich-text editor.

    ``validate_length`` counts the raw stored string, which for rich text is
    markup: bolding three words in a 480-character blurb adds ~30 characters
    of ``<strong>`` and pushes it over a 500-character cap the writer cannot
    see. This counts what a reader actually reads, and allows the longer text
    a treatment blurb needs now that it has formatting at all.
    """
    if not value:
        return

    from django.utils.html import strip_tags
    from html import unescape

    # `&nbsp;` and friends are one character to a reader and six to `len`.
    text = unescape(strip_tags(value)).strip()

    MinLengthValidator(min_length, message=f"محتوا باید حداقل {min_length} کاراکتر باشد")(text)
    MaxLengthValidator(max_length, message=f"محتوا نباید بیشتر از {max_length} کاراکتر باشد")(text)


def validate_phone(value):
    """
    Validate an Iranian phone number: 11 digits starting with 0.

    Accepts both mobile (``09XXXXXXXXX``) and landline (``0AXXXXXXXXX`` where
    ``A`` is the area-code prefix, e.g. ``021...``, ``051...``, ``024...``).
    Rejects international-format numbers and anything shorter/longer.
    """
    if not value:
        return

    value = value.strip()

    RegexValidator(
        regex=r'^0\d{10}$',
        message="شماره تلفن باید 11 رقم و با 0 شروع شود (موبایل یا ثابت)",
    )(value)


def validate_national_code(value):
    """
    Validate an Iranian national ID (کد ملی) by its check digit.

    A length-only check would accept any ten digits, so typos in a booking
    would only surface at the clinic desk. The official algorithm weights the
    first nine digits by 10..2, takes the sum modulo 11, and compares against
    the tenth digit: remainders below 2 must equal it, otherwise 11 minus the
    remainder must.

    Repdigit codes ("0000000000", "1111111111", ...) satisfy the checksum by
    coincidence and are rejected explicitly.
    """
    if not value:
        return

    value = value.strip()

    RegexValidator(
        regex=r'^\d{10}$',
        message="کد ملی باید دقیقاً ۱۰ رقم باشد",
    )(value)

    if value == value[0] * 10:
        raise ValidationError("کد ملی وارد شده معتبر نیست")

    checksum = sum(int(digit) * (10 - index) for index, digit in enumerate(value[:9]))
    remainder = checksum % 11
    control = int(value[9])

    valid = control == remainder if remainder < 2 else control == 11 - remainder
    if not valid:
        raise ValidationError("کد ملی وارد شده معتبر نیست")