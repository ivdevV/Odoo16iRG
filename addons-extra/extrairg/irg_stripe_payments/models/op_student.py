# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class OpStudent(models.Model):
    _inherit = 'op.student'

    irg_stripe_payment_count = fields.Integer(
        string='Nº de pagos Stripe',
        compute='_compute_irg_stripe_payment_count',
    )

    @api.depends('partner_id')
    def _compute_irg_stripe_payment_count(self):
        """Conteo por contacto.

        `op.student` hace `_inherits` de `res.partner`, así que `partner_id` siempre
        está presente y es el eje correcto para agrupar los pagos.
        """
        payment_obj = self.env['irg.stripe.payment'].sudo()
        grouped = payment_obj.read_group(
            [('partner_id', 'in', self.mapped('partner_id').ids)],
            ['partner_id'],
            ['partner_id'],
        )
        counts = {row['partner_id'][0]: row['partner_id_count'] for row in grouped}
        for student in self:
            student.irg_stripe_payment_count = counts.get(student.partner_id.id, 0)

    def action_irg_view_stripe_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Pagos Stripe de %s") % self.name,
            'res_model': 'irg.stripe.payment',
            'view_mode': 'tree,form,pivot',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id},
        }
