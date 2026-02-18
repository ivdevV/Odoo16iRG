from odoo import fields, models


class Slide(models.Model):
    _inherit = 'slide.slide'

    allowed_batch_ids = fields.Many2many(
        'op.batch',
        'slide_allowed_batch_rel',
        'slide_id',
        'batch_id',
        string='Lotes Permitidos',
        help='Si se seleccionan lotes, solo esos lotes podrán acceder a este contenido.'
    )

    def is_user_allowed_by_batch(self, user):
        self.ensure_one()

        if not self.allowed_batch_ids:
            return True

        if not user or user._is_public():
            return False

        partner = user.partner_id
        if not partner or not self.channel_id:
            return False

        domain = [
            ('partner_id', '=', partner.id),
            ('channel_id', '=', self.channel_id.id),
            ('active', '=', True),
            ('batch_id', 'in', self.allowed_batch_ids.ids),
        ]
        return bool(self.env['slide.channel.partner'].sudo().search_count(domain))
