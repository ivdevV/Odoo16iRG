# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# XML IDs de los únicos tipos permitidos en este despliegue.
_ALLOWED_XML_IDS = [
    'irg_identification_types.it_dni',
    'irg_identification_types.it_pasaporte',
    'irg_identification_types.it_documento_identificativo',
]


class L10nLatamIdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'

    def _get_allowed_ids(self):
        """Devuelve los IDs de los 3 tipos permitidos (sólo los que ya existen en DB)."""
        ids = []
        for xml_id in _ALLOWED_XML_IDS:
            rec = self.env.ref(xml_id, raise_if_not_found=False)
            if rec:
                ids.append(rec.id)
        return ids

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """Restringe el desplegable a los 3 tipos IRG.

        Solo afecta a la selección interactiva; no toca el renderizado de
        registros existentes, por lo que partners con un tipo legacy asignado
        seguirán mostrando su valor actual sin perderlo.
        """
        allowed = self._get_allowed_ids()
        args = list(args or []) + [('id', 'in', allowed)]
        return super()._name_search(
            name=name,
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )
