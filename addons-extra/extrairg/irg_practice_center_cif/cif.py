# -*- coding: utf-8 -*-


def resolve_center_cif(cif, partner_vat=False):
    """Devuelve el CIF del centro si tiene texto; si no, el VAT del contacto."""
    cleaned = (cif or "").strip()
    if cleaned:
        return cleaned
    fallback = (partner_vat or "").strip()
    return fallback or False
