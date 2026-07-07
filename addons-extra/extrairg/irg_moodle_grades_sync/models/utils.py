import re
import unicodedata


def normalize_name(value):
    """Lowercase, strip accents and collapse whitespace for name matching."""
    if not value:
        return ''
    text = unicodedata.normalize('NFKD', str(value))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    return re.sub(r'\s+', ' ', text)


def parse_grade(raw):
    """Best-effort parse of a Moodle grade string into a float.

    Moodle may return '8,50', '8.50', '85 %', or non-numeric scales ('Apto').
    Returns None when the value is not numeric.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text == '-':
        return None
    text = text.replace('%', '').strip().replace(',', '.')
    try:
        return float(text)
    except (ValueError, TypeError):
        return None
