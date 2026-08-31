# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
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
             "pagos se vinculen solos. Un contacto puede tener varios Customers: "
             "añadir uno nuevo no sustituye a los que ya tuviera.",
    )
    note = fields.Text(string='Nota')

    impact_preview = fields.Text(
        string='Qué va a pasar', compute='_compute_impact_preview', readonly=True)

    @api.depends('review_id', 'partner_id')
    def _compute_impact_preview(self):
        """Anticipa el alcance antes de confirmar.

        Existe porque el asistente dejaba "resolver" revisiones de
        ``conflicting_customer_id`` que no llevan ningún pago, sin cambiar nada y sin
        avisar. Ver el número de antemano evita esa resolución fantasma.
        """
        for wizard in self:
            review = wizard.review_id
            if not review:
                wizard.impact_preview = ''
                continue
            payments = review.payment_ids
            if review.stripe_customer_id:
                payments |= self.env['irg.stripe.payment'].sudo().search([
                    ('stripe_customer_id', '=', review.stripe_customer_id)])
            movable = payments.filtered(
                lambda p: not p.partner_id or (
                    wizard.partner_id and p.partner_id == wizard.partner_id))
            lines = [
                _("Pagos que se vincularán: %s") % len(movable),
                _("Otras revisiones del mismo Customer que se cerrarán: %s")
                % len(review._irg_sibling_reviews()),
            ]
            blocked = len(payments) - len(movable)
            if blocked:
                lines.append(_(
                    "Pagos que NO se tocan por pertenecer ya a otro contacto: %s") % blocked)
            if not movable and not review._irg_sibling_reviews():
                lines.append(_(
                    "Aviso: esta revisión no tiene pagos asociados. Resolverla solo "
                    "registrará el Customer bajo el contacto."))
            wizard.impact_preview = '\n'.join(lines)

    def action_confirm(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Hay que seleccionar un contacto."))
        # El control de acceso lo hace `_irg_apply_partner` en servidor: ocultar el
        # botón en la vista no es seguridad.
        self.review_id._irg_apply_partner(
            self.partner_id, note=self.note, link_customer=self.link_customer_id)
        return {'type': 'ir.actions.act_window_close'}
