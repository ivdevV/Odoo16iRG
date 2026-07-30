# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    # El `required=True` que traían isep_record_request e isep_openeducat_custom es
    # la causa raíz de las fechas inventadas: el código no podía guardar la admisión
    # sin fecha, así que escribía un 01/01/2000 para salir del paso. Un hueco visible
    # es preferible a un dato falso indistinguible de uno real.
    #
    # El campo sigue siendo related no almacenado de partner_id.birth_date; aquí solo
    # se relaja la obligatoriedad.
    birth_date = fields.Date(
        related='partner_id.birth_date',
        required=False,
        string='Fecha de nacimiento',
    )

    @api.constrains('birth_date')
    def _check_birthdate(self):
        """El constraint del core no contempla el campo vacío.

        `openeducat_admission` hace `if record.birth_date > fields.Date.today()`,
        que con `False` lanza `TypeError: '>' not supported between instances of
        'bool' and 'datetime.date'`. Al dejar de ser obligatorio el campo, ese caso
        pasa a ser normal, así que hay que saltarlo.
        """
        for record in self:
            if not record.birth_date:
                continue
            if record.birth_date > fields.Date.today():
                raise ValidationError(_(
                    "La fecha de nacimiento no puede ser posterior a hoy."))
