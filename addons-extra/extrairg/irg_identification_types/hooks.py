# -*- coding: utf-8 -*-
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# Mapa xml_id → nombre canónico que debe tener el registro en BD.
# Se aplica en cada instalación Y en cada -u, independientemente del flag
# noupdate que haya guardado Odoo en ir.model.data.
_CANONICAL_NAMES = {
    'irg_identification_types.it_dni': 'DNI',
    'irg_identification_types.it_pasaporte': 'Pasaporte',
    'irg_identification_types.it_documento_identificativo': 'Documento de identificación personal',
}


def post_migrate(env, version_from, version_to):
    """
    Ejecutado en cada instalación (-i) y en cada actualización (-u).
    Garantiza que los 3 tipos tengan siempre el nombre correcto,
    sin importar el flag noupdate almacenado en ir.model.data.
    """
    for xml_id, name in _CANONICAL_NAMES.items():
        rec = env.ref(xml_id, raise_if_not_found=False)
        if rec and rec.name != name:
            rec.write({'name': name})
            _logger.info(
                'irg_identification_types: nombre actualizado "%s" → "%s"',
                rec.name, name,
            )
