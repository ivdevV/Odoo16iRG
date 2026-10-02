from decimal import Decimal, ROUND_HALF_UP

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .irg_tfm_logic import DELIVERY_STAGE_DATES, DELIVERY_STAGE_LABELS


class IrgTfmConvocatoria(models.Model):
    _name = 'irg.tfm.convocatoria'
    _description = 'Convocatoria TFM'
    _order = 'code'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    partial_provisional_open_date = fields.Date(
        string='Apertura provisional del borrador',
    )
    partial_provisional_close_date = fields.Date(
        string='Cierre provisional del borrador',
    )
    partial_open_date = fields.Date(string='Apertura final del borrador')
    partial_close_date = fields.Date(string='Cierre final del borrador')
    final_provisional_open_date = fields.Date(
        string='Apertura provisional del depósito',
    )
    final_provisional_close_date = fields.Date(
        string='Cierre provisional del depósito',
    )
    final_open_date = fields.Date(string='Apertura final del depósito')
    final_close_date = fields.Date(string='Cierre final del depósito')
    weight_tutor = fields.Float(string='Peso nota del tutor (%)', digits=(16, 2))
    weight_draft = fields.Float(string='Peso nota del borrador (%)', digits=(16, 2))
    weight_defense = fields.Float(string='Peso nota de defensa (%)', digits=(16, 2))

    _sql_constraints = [
        ('irg_tfm_convocatoria_code_unique', 'unique(code)',
         'El código de convocatoria debe ser único.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].strip().upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('code'):
            vals = dict(vals, code=vals['code'].strip().upper())
        return super().write(vals)

    @api.constrains(
        'partial_provisional_open_date', 'partial_provisional_close_date',
        'partial_open_date', 'partial_close_date',
        'final_provisional_open_date', 'final_provisional_close_date',
        'final_open_date', 'final_close_date',
    )
    def _check_delivery_windows(self):
        labels = dict(DELIVERY_STAGE_LABELS)
        for record in self:
            for stage, (open_field, close_field) in DELIVERY_STAGE_DATES.items():
                opening = record[open_field]
                closing = record[close_field]
                if opening and closing and opening > closing:
                    raise ValidationError(
                        _('The opening date cannot be after the closing date for %s.')
                        % labels[stage]
                    )

    @api.constrains('weight_tutor', 'weight_draft', 'weight_defense')
    def _check_component_weights(self):
        for record in self:
            weights = (
                record.weight_tutor,
                record.weight_draft,
                record.weight_defense,
            )
            if all(not weight for weight in weights):
                continue
            if any(weight < 0 for weight in weights):
                raise ValidationError(_('Las ponderaciones no pueden ser negativas.'))
            total = sum(
                (Decimal(str(weight)) for weight in weights),
                Decimal('0'),
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if total != Decimal('100.00'):
                raise ValidationError(_(
                    'Las ponderaciones del tutor, el borrador y la defensa deben sumar 100.'
                ))
