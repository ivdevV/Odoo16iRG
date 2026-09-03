# -*- coding: utf-8 -*-

IRG_ONLINE_MASTER_PRACTICE_TYPES = (
    'validation',
    'tfm_validation',
    'homeclass_asincronas',
)


def irg_batch_code_is_online_master(code):
    """True when the batch code is an online master, including MONLONL.

    MONLHC / MONLPRS start with ONL inside the Neurologopedia prefix, so they
    are excluded. A bare substring check of MONL would drop the real online
    variant MONLONL.
    """
    normalized = (code or '').strip().upper()
    if not normalized:
        return False
    if normalized.startswith('MONLHC') or normalized.startswith('MONLPRS'):
        return False
    return 'ONL' in normalized
