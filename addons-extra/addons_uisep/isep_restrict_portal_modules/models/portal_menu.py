from odoo import api, fields, models


class PortalMenu(models.Model):
    _inherit = 'openeducat.portal.menu'

    requires_completing_half = fields.Boolean(default=False, string='¿Requiere completar un porcentaje?')
    percentage = fields.Float(string='Porcentaje', digits=(5, 2))

    @api.onchange('requires_completing_half')
    def _onchange_requires_completing_half(self):
        if not self.requires_completing_half:
            self.percentage = False
