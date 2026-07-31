# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    irg_stripe_payment_ids = fields.One2many(
        'irg.stripe.payment',
        'partner_id',
        string='Pagos Stripe',
    )
    irg_stripe_payment_count = fields.Integer(
        string='Nº de pagos Stripe',
        compute='_compute_irg_stripe_payment_totals',
    )
    irg_stripe_paid_total = fields.Monetary(
        string='Total pagado en Stripe',
        currency_field='irg_stripe_payment_currency_id',
        compute='_compute_irg_stripe_payment_totals',
    )
    irg_stripe_payment_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda de pagos Stripe',
        compute='_compute_irg_stripe_payment_totals',
    )

    # Una persona puede tener varios Customers en Stripe: dos tarjetas, dos
    # checkouts, un Payment Link que crea uno nuevo. El `Char`
    # `irg_stripe_customer_id` de irg_payment_stripe_recurring solo admite uno, y por
    # eso el segundo Customer de alguien acababa en la cola de revisión como si fuera
    # un conflicto. Aquí caben todos.
    irg_stripe_customer_ids = fields.One2many(
        'irg.stripe.customer',
        'partner_id',
        string='Customers de Stripe',
    )
    irg_stripe_customer_count = fields.Integer(
        string='Nº de Customers Stripe',
        compute='_compute_irg_stripe_customer_count',
    )

    @api.depends('irg_stripe_customer_ids')
    def _compute_irg_stripe_customer_count(self):
        for partner in self:
            partner.irg_stripe_customer_count = len(partner.irg_stripe_customer_ids)

    @api.depends('irg_stripe_payment_ids.amount',
                 'irg_stripe_payment_ids.amount_refunded',
                 'irg_stripe_payment_ids.state')
    def _compute_irg_stripe_payment_totals(self):
        """Total neto cobrado, en la moneda de la compañía.

        Se suman solo los pagos efectivamente cobrados y se descuenta lo reembolsado.
        Los pagos en una divisa distinta a la de la compañía se convierten; si la
        divisa del pago no existe en Odoo (`currency_id` vacío) el importe se ignora
        en el total, porque convertirlo sería inventárselo.
        """
        company_currency = self.env.company.currency_id
        today = fields.Date.context_today(self)
        for partner in self:
            total = 0.0
            payments = partner.irg_stripe_payment_ids.filtered(
                lambda p: p.state in ('succeeded', 'refunded', 'partially_refunded'))
            for payment in payments:
                if not payment.currency_id:
                    continue
                net = payment.amount - payment.amount_refunded
                if payment.currency_id == company_currency:
                    total += net
                else:
                    total += payment.currency_id._convert(
                        net, company_currency, partner.company_id or self.env.company,
                        payment.payment_date or today, round=False)
            partner.irg_stripe_payment_count = len(partner.irg_stripe_payment_ids)
            partner.irg_stripe_paid_total = total
            partner.irg_stripe_payment_currency_id = company_currency

    def action_irg_view_stripe_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Pagos Stripe de %s") % self.name,
            'res_model': 'irg.stripe.payment',
            'view_mode': 'tree,form,pivot',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id, 'search_default_group_by_state': 1},
        }
