# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class IrgDiscountException(models.Model):
    _name = 'irg.discount.exception'
    _description = 'Excepciones de precio para Convenio'

    name = fields.Char(string='Nombre', required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Plantilla de Producto')
    product_id = fields.Many2one('product.product', string='Producto')
    price_exception = fields.Float(string='Precio (sin impuestos)', required=True)
    active = fields.Boolean(string='Activo', default=True)
    date_from = fields.Date(string='Válido desde')
    date_to = fields.Date(string='Válido hasta')
    note = fields.Text(string='Nota')

    @api.constrains('product_tmpl_id', 'product_id')
    def _check_product(self):
        for rec in self:
            if not rec.product_id and not rec.product_tmpl_id:
                raise ValidationError(_('Debe especificar un producto o una plantilla.'))

    def get_active_for_product(self, product):
        """Devuelve la excepción activa (si existe) para el producto dado."""
        today = fields.Date.context_today(self)
        # Buscar por producto o plantilla, luego validar fechas en Python para evitar dominios complejos
        domain = [
            ('active', '=', True),
            ('price_exception', '>', 0.0),
            '|', ('product_id', '=', product.id), ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ]
        candidates = self.search(domain)
        for cand in candidates:
            if cand.date_from and cand.date_from > today:
                continue
            if cand.date_to and cand.date_to < today:
                continue
            return cand
        return self.browse()
