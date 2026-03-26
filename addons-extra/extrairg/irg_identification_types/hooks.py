# -*- coding: utf-8 -*-
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# External IDs que CREA este módulo — no se desactivarán
_OUR_XML_IDS = [
    'irg_identification_types.it_dni',
    'irg_identification_types.it_pasaporte',
    'irg_identification_types.it_documento_identificativo',
]

# Tipos upstream bien conocidos → tipo equivalente en este módulo
# Sirve para reasignar los partners antes de desactivar los tipos legacy.
_MIGRATION_MAP = {
    'l10n_latam_base.it_vat': 'irg_identification_types.it_documento_identificativo',
    'l10n_latam_base.it_pass': 'irg_identification_types.it_pasaporte',
}


def post_init_hook(cr, registry):
    """
    Ejecutado una vez al instalar el módulo:
    1. Reasigna partners cuyo tipo de identificación sea un tipo legacy conocido.
    2. Desactiva todos los tipos que no pertenezcan a este módulo.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    IdType = env['l10n_latam.identification.type'].with_context(active_test=False)
    Partner = env['res.partner'].with_context(active_test=False)

    # Resuelve los IDs de nuestros 3 registros
    our_ids = set()
    for xml_id in _OUR_XML_IDS:
        rec = env.ref(xml_id, raise_if_not_found=False)
        if rec:
            our_ids.add(rec.id)

    # Migra partners desde tipos legacy a los nuestros equivalentes
    for src_xml_id, dst_xml_id in _MIGRATION_MAP.items():
        src = env.ref(src_xml_id, raise_if_not_found=False)
        dst = env.ref(dst_xml_id, raise_if_not_found=False)
        if not src or not dst or src.id in our_ids:
            continue
        partners = Partner.search([('l10n_latam_identification_type_id', '=', src.id)])
        if partners:
            partners.write({'l10n_latam_identification_type_id': dst.id})
            _logger.info(
                'irg_identification_types: migrados %d partner(s) de "%s" → "%s"',
                len(partners),
                src.name,
                dst.name,
            )

    # Desactiva todos los tipos que no son los nuestros
    to_deactivate = IdType.search([('id', 'not in', list(our_ids))])
    if to_deactivate:
        to_deactivate.write({'active': False})
        _logger.info(
            'irg_identification_types: desactivados %d tipo(s) de identificación: %s',
            len(to_deactivate),
            to_deactivate.mapped('name'),
        )
