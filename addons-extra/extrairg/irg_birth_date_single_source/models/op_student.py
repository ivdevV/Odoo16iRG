# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OpStudent(models.Model):
    _inherit = 'op.student'

    # `op.student` ya hace `_inherits = {'res.partner': 'partner_id'}`, así que esta
    # fecha se heredaría sola del contacto. La columna propia existe únicamente
    # porque `openeducat_core` declara el campo y tapa la delegación; de ahí que
    # pudieran divergir.
    #
    # `store=True` es obligatorio, no una preferencia: hay informes que leen
    # `op_student.birth_date` con SQL crudo (p. ej. isep_control_escolar
    # /models/student_report.py). Con `store=False` la columna se quedaría
    # congelada con el valor viejo y esos informes mentirían en silencio.
    #
    # `readonly=False` hace que editar la fecha en la ficha del alumno escriba en
    # el contacto, que es justo lo que se quiere: un único dato, editable desde
    # los dos sitios.
    birth_date = fields.Date(
        related='partner_id.birth_date',
        store=True,
        readonly=False,
        string='Fecha de nacimiento',
    )

    irg_birth_date_missing = fields.Boolean(
        string='Sin fecha de nacimiento',
        compute='_compute_irg_birth_date_missing',
        search='_search_irg_birth_date_missing',
        help="Verdadero si el alumno no tiene una fecha de nacimiento utilizable. "
             "Incluye los valores fabricados por el código antiguo.",
    )

    #: Valores que el código antiguo escribía cuando no encontraba fecha real.
    #: No son datos: son huecos disfrazados de dato.
    IRG_FABRICATED_BIRTH_DATE = '2000-01-01'
    IRG_PLAUSIBLE_BEFORE = '2020-01-01'

    def _irg_birth_date_is_usable(self):
        """La fecha existe y no es uno de los valores inventados conocidos."""
        self.ensure_one()
        if not self.birth_date:
            return False
        as_string = fields.Date.to_string(self.birth_date)
        if as_string == self.IRG_FABRICATED_BIRTH_DATE:
            return False
        if as_string >= self.IRG_PLAUSIBLE_BEFORE:
            # Nadie matriculado nació después de 2020. Este patrón corresponde al
            # antiguo fallback que guardaba la fecha de creación del registro.
            return False
        return True

    @api.depends('birth_date')
    def _compute_irg_birth_date_missing(self):
        for student in self:
            student.irg_birth_date_missing = not student._irg_birth_date_is_usable()

    @api.constrains('birth_date')
    def _check_birthdate(self):
        """Mismo problema que en op.admission: el constraint del core no admite vacío.

        `openeducat_core` hace `if record.birth_date > fields.Date.today()`, que con
        `False` lanza `TypeError`. Ahora que la fecha puede faltar legítimamente, hay
        que saltar ese caso en vez de reventar.
        """
        for record in self:
            if not record.birth_date:
                continue
            if record.birth_date > fields.Date.today():
                raise ValidationError(_(
                    "La fecha de nacimiento no puede ser posterior a hoy."))

    def _search_irg_birth_date_missing(self, operator, value):
        if operator not in ('=', '!='):
            raise ValueError("Operador no soportado para irg_birth_date_missing: %s" % operator)
        missing_domain = [
            '|', '|',
            ('birth_date', '=', False),
            ('birth_date', '=', self.IRG_FABRICATED_BIRTH_DATE),
            ('birth_date', '>=', self.IRG_PLAUSIBLE_BEFORE),
        ]
        looking_for_missing = bool(value) if operator == '=' else not value
        if looking_for_missing:
            return missing_domain
        return [
            '&', '&',
            ('birth_date', '!=', False),
            ('birth_date', '!=', self.IRG_FABRICATED_BIRTH_DATE),
            ('birth_date', '<', self.IRG_PLAUSIBLE_BEFORE),
        ]
