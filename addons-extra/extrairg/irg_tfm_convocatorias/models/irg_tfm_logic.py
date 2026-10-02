"""Reglas puras del TFM. Sin importar Odoo, para probarlas sin el runtime."""
import re
from decimal import Decimal, ROUND_HALF_UP


COMPONENT_KEYS = ('tutor', 'draft', 'defense')
DELIVERY_STAGE_LABELS = (
    ('partial_provisional', 'Borrador: entrega provisional'),
    ('partial', 'Borrador: entrega final'),
    ('final_provisional', 'Depósito: entrega provisional'),
    ('final', 'Depósito: entrega final'),
)
DELIVERY_STAGES = tuple(stage for stage, _label in DELIVERY_STAGE_LABELS)
DELIVERY_STAGE_DATES = {
    'partial_provisional': (
        'partial_provisional_open_date', 'partial_provisional_close_date',
    ),
    'partial': ('partial_open_date', 'partial_close_date'),
    'final_provisional': (
        'final_provisional_open_date', 'final_provisional_close_date',
    ),
    'final': ('final_open_date', 'final_close_date'),
}
MAX_FEEDBACK_BYTES = 20 * 1024 * 1024
_FEEDBACK_EXTENSIONS = {'pdf', 'doc', 'docx'}


class TfmRuleError(ValueError):
    """Entrada que no cumple una regla de negocio del TFM."""


def score_is_valid(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    if number != number or number in (float('inf'), float('-inf')):
        return False
    return number == 0 or 1 <= number <= 10


def weighted_points(notes, weights):
    """Devuelve el punteo con 2 decimales, o None si falta alguna nota.

    ``weights`` son porcentajes. Tienen que sumar 100.00.
    """
    if any(notes.get(key) is None for key in COMPONENT_KEYS):
        return None
    if any(not score_is_valid(notes.get(key)) for key in COMPONENT_KEYS):
        raise TfmRuleError('score')
    weight_values = []
    for key in COMPONENT_KEYS:
        try:
            weight_values.append(Decimal(str(weights[key])))
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise TfmRuleError('weights') from exc
    total_weight = sum(weight_values, Decimal('0')).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP,
    )
    if total_weight != Decimal('100.00'):
        raise TfmRuleError('weights')
    total = Decimal('0')
    for key, weight in zip(COMPONENT_KEYS, weight_values):
        total += Decimal(str(notes[key])) * weight / Decimal('100')
    return float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def effective_dates(base_open, base_close, override_open, override_close):
    """La fecha del alumno sustituye a la de la convocatoria solo si está puesta."""
    return (
        override_open if override_open else base_open,
        override_close if override_close else base_close,
    )


def window_is_open(opening, closing, today):
    return bool(opening and closing and opening <= today <= closing)


def render_outline_text(version, questions):
    lines = ['Esquema TFM', 'Versión: %s' % version, '']
    for question in questions:
        section = (question.get('section') or '').strip()
        title = (question.get('title') or '').strip()
        answer = question.get('answer') or 'Sin respuesta'
        if section:
            lines.append(section)
        lines.append(title)
        lines.append(str(answer))
        lines.append('')
    return '\n'.join(lines).strip() + '\n'


_HC_BATCH_RE = re.compile(r'HC(\d{4})', re.IGNORECASE)
_ONL_QUARTER_RE = re.compile(r'ONL(\d{2})([1-4])(?!\d)', re.IGNORECASE)
_ONL_FIRST_CONVOCATION = 262


def irg_parse_tfm_batch_eligibility(code):
    """Devuelve (modalidad, token) o False.

    HomeClass sigue en AAMM: HC desde 2511 y MONLHC desde 2601.
    Online usa el código de las 4 convocatorias anuales, AA más un dígito
    del 1 al 4. El primero que entra es 262, la segunda de 2026.
    Cualquier código que contenga PRS queda fuera.
    """
    if not code or 'PRS' in code.upper():
        return False
    normalized = code.upper()
    if 'MONLHC' in normalized:
        return _hc_batch_eligibility(normalized, 2601)
    quarter = _ONL_QUARTER_RE.search(normalized)
    if quarter:
        token = int(quarter.group(1) + quarter.group(2))
        return ('ONL', token) if token >= _ONL_FIRST_CONVOCATION else False
    return _hc_batch_eligibility(normalized, 2511)


def _hc_batch_eligibility(normalized, minimum):
    match = _HC_BATCH_RE.search(normalized)
    if not match:
        return False
    yymm = int(match.group(1))
    month = yymm % 100
    if not 1 <= month <= 12:
        return False
    return ('HC', yymm) if yymm >= minimum else False


def safe_feedback_name(filename, size):
    name = (filename or '').replace('\\', '/').split('/')[-1].strip()
    if not name or '.' not in name or '/' in name or '\\' in name:
        raise TfmRuleError('filename')
    extension = name.rsplit('.', 1)[-1].lower()
    if extension not in _FEEDBACK_EXTENSIONS:
        raise TfmRuleError('filename')
    if size is None or size < 1 or size > MAX_FEEDBACK_BYTES:
        raise TfmRuleError('size')
    return name
