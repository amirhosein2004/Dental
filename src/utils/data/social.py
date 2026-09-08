"""
Social handle <-> profile URL conversion.

Doctors type only their username (``dr.saeedebabaee``); the DB keeps the full
URL so every consumer template can use the value directly as an ``href``
without knowing which platform it belongs to.
"""
import re

from django.core.exceptions import ValidationError


# platform -> (base URL, human-readable prefix shown next to the input)
PLATFORMS = {
    'instagram': ('https://instagram.com/', 'instagram.com/'),
    'telegram': ('https://t.me/', 't.me/'),
    'twitter': ('https://twitter.com/', 'twitter.com/'),
    'linkedin': ('https://www.linkedin.com/in/', 'linkedin.com/in/'),
}

# Handles across these platforms are letters, digits, dot, underscore, hyphen.
_HANDLE_RE = re.compile(r'^[A-Za-z0-9._-]{1,100}$')


def to_handle(url, platform):
    """
    Reduce a stored URL back to the bare handle, for pre-filling the form.

    Unrecognised values are returned unchanged so a legacy row with an odd URL
    stays visible and editable instead of silently blanking.
    """
    if not url:
        return ''
    value = url.strip()
    base, _label = PLATFORMS[platform]

    # Compare host-insensitively: older rows may use www./http/x.com variants.
    stripped = re.sub(r'^https?://', '', value, flags=re.IGNORECASE)
    stripped = re.sub(r'^www\.', '', stripped, flags=re.IGNORECASE)
    base_path = re.sub(r'^https?://(www\.)?', '', base, flags=re.IGNORECASE)

    if stripped.lower().startswith(base_path.lower()):
        return stripped[len(base_path):].strip('/')

    # Some other host for the same platform (e.g. x.com for twitter): fall back
    # to the last path segment, which is the handle on all four platforms.
    if '/' in stripped:
        return stripped.rstrip('/').rsplit('/', 1)[-1]
    return value


def to_url(handle, platform):
    """
    Build the canonical profile URL from user input.

    Accepts a bare handle, ``@handle``, or a full pasted URL — people paste
    what's in their address bar regardless of what the label asks for.
    Returns '' for empty input so the field stays optional.

    Raises ValidationError when the handle contains characters no platform
    allows, which usually means a whole URL with query junk was pasted.
    """
    if not handle:
        return ''

    base, _label = PLATFORMS[platform]
    value = handle.strip()

    # Tolerate a pasted URL by reducing it to its handle first.
    if '://' in value or '/' in value or value.lower().startswith('www.'):
        value = to_handle(value, platform)

    value = value.lstrip('@').strip('/')
    # Drop any query string / fragment (…?igsh=…, …?utm_source=…).
    value = re.split(r'[?#]', value)[0]

    if not value:
        return ''
    if not _HANDLE_RE.match(value):
        raise ValidationError(
            'شناسه فقط می‌تواند شامل حروف انگلیسی، اعداد، نقطه، خط‌تیره و آندرلاین باشد'
        )
    return base + value
