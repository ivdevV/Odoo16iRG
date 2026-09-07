from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrgTfmConvocatoria(models.Model):
    _name = 'irg.tfm.convocatoria'
    _description = 'Convocatoria TFM'
    _order = 'code'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    partial_open_date = fields.Date(string='Apertura entrega parcial')
    partial_close_date = fields.Date(string='Cierre entrega parcial')
    final_open_date = fields.Date(string='Apertura entrega final')
    final_close_date = fields.Date(string='Cierre entrega final')

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
        'partial_open_date', 'partial_close_date',
        'final_open_date', 'final_close_date',
    )
    def _check_delivery_windows(self):
        for record in self:
            for opening, closing, label in (
                (record.partial_open_date, record.partial_close_date, _('partial delivery')),
                (record.final_open_date, record.final_close_date, _('final delivery')),
            ):
                if opening and closing and opening > closing:
                    raise ValidationError(
                        _('The opening date cannot be after the closing date for %s.') % label
                    )
