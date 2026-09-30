from decimal import Decimal, ROUND_HALF_UP

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrgTfmConvocatoria(models.Model):
    _name = 'irg.tfm.convocatoria'
    _description = 'Convocatoria TFM'
    _order = 'code'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    preliminary_open_date = fields.Date(
        string='Apertura observaciones previas',
    )
    preliminary_close_date = fields.Date(
        string='Cierre observaciones previas',
    )
    partial_open_date = fields.Date(string='Apertura entrega parcial')
    partial_close_date = fields.Date(string='Cierre entrega parcial')
    final_open_date = fields.Date(string='Apertura entrega final')
    final_close_date = fields.Date(string='Cierre entrega final')
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
        'preliminary_open_date', 'preliminary_close_date',
        'partial_open_date', 'partial_close_date',
        'final_open_date', 'final_close_date',
    )
    def _check_delivery_windows(self):
        for record in self:
            for opening, closing, label in (
                (
                    record.preliminary_open_date,
                    record.preliminary_close_date,
                    _('observaciones previas'),
                ),
                (record.partial_open_date, record.partial_close_date, _('partial delivery')),
                (record.final_open_date, record.final_close_date, _('final delivery')),
            ):
                if opening and closing and opening > closing:
                    raise ValidationError(
                        _('The opening date cannot be after the closing date for %s.') % label
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
