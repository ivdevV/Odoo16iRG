# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class IrgStripeIdentityLinkWizard(models.TransientModel):
    _name = 'irg.stripe.identity.link.wizard'
    _description = 'Vincular pago Stripe a un contacto'

    review_id = fields.Many2one(
        'irg.stripe.identity.review', string='Revisión', required=True, readonly=True)
    stripe_customer_id = fields.Char(related='review_id.stripe_customer_id', readonly=True)
    stripe_email = fields.Char(related='review_id.stripe_email', readonly=True)
    candidate_partner_ids = fields.Many2many(
        related='review_id.candidate_partner_ids', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Contacto', required=True)
    link_customer_id = fields.Boolean(
        string='Guardar el Customer ID en el contacto',
        default=True,
        help="Deja el Customer de Stripe asociado al contacto para que los próximos "
             "pagos se vinculen solos.",
    )
    note = fields.Text(string='Nota')

    def action_confirm(self):
        self.ensure_one()
        # El control de acceso va en servidor: ocultar el botón no es seguridad.
        self.review_id._check_can_resolve()

        if not self.partner_id:
            raise UserError(_("Hay que seleccionar un contacto."))

        payments = self.review_id.payment_ids
        if payments:
            payments.sudo().write({
                'partner_id': self.partner_id.id,
                'partner_match_method': 'manual',
                'partner_state': 'linked',
            })

        if self.link_customer_id and self.stripe_customer_id:
            existing = self.partner_id.sudo().irg_stripe_customer_id
            if existing and existing != self.stripe_customer_id:
                raise UserError(_(
                    "El contacto %(partner)s ya está asociado al Customer %(existing)s. "
                    "Resuelve primero ese conflicto o desmarca la casilla de guardar el "
                    "Customer ID.",
                    partner=self.partner_id.display_name,
                    existing=existing,
                ))
            if not existing:
                self.partner_id.sudo().write(
                    {'irg_stripe_customer_id': self.stripe_customer_id})

        self.review_id.write({
            'partner_id': self.partner_id.id,
            'state': 'resolved',
            'resolution_note': self.note or self.review_id.resolution_note,
            'resolved_by_id': self.env.user.id,
            'resolved_at': fields.Datetime.now(),
        })
        return {'type': 'ir.actions.act_window_close'}
