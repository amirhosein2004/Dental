"""
Phone-number parsing and normalisation for bulk sending.

Staff paste numbers from wherever they keep them — a spreadsheet column, a
WhatsApp message, a printed list. The separators, the leading +98, and the
duplicates are all somebody else's formatting problem, so normalise once here
and let the rest of the system assume clean 11-digit strings.
"""
import re

# Split on anything that is not a digit or a plus sign: commas, spaces,
# newlines, tabs, semicolons, Persian commas ("،") all work.
_SPLIT_RE = re.compile(r'[^\d+]+')

# Persian and Arabic-Indic digits map onto ASCII so pasted Persian numerals work.
_DIGIT_MAP = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')

_VALID_RE = re.compile(r'^0\d{10}$')


def normalize(number):
    """
    Reduce one number to canonical ``0XXXXXXXXXX`` form, or None if it cannot be.

    Handles the three ways an Iranian mobile gets written down:
    ``+989123456789``, ``00989123456789``, ``9123456789`` — all become
    ``09123456789``.
    """
    if not number:
        return None

    digits = number.translate(_DIGIT_MAP).strip()
    digits = re.sub(r'[^\d+]', '', digits)

    if digits.startswith('+98'):
        digits = '0' + digits[3:]
    elif digits.startswith('0098'):
        digits = '0' + digits[4:]
    elif digits.startswith('98') and len(digits) == 12:
        digits = '0' + digits[2:]
    elif len(digits) == 10 and digits.startswith('9'):
        # Written without the leading zero.
        digits = '0' + digits

    return digits if _VALID_RE.match(digits) else None


def parse_numbers(raw):
    """
    Turn a pasted blob into ``(valid_numbers, invalid_tokens)``.

    Order is preserved and duplicates dropped, so the operator sees the list
    they typed minus the noise — and gets told exactly which tokens were
    rejected rather than silently losing them.
    """
    if not raw:
        return [], []

    seen = set()
    valid = []
    invalid = []

    for token in _SPLIT_RE.split(raw):
        if not token:
            continue
        number = normalize(token)
        if number is None:
            invalid.append(token)
            continue
        if number in seen:
            continue
        seen.add(number)
        valid.append(number)

    return valid, invalid
