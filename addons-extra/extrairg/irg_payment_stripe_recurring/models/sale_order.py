# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    stripe_subscription_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('past_due', 'Past Due'),
            ('paused', 'Paused'),
            ('canceled', 'Canceled'),
        ],
        string='Stripe Subscription State',
        default='draft',
        tracking=True,
        copy=False,
    )
    stripe_subscription_ref = fields.Char(
        string='Stripe Subscription Ref',
        copy=False,
    )
    stripe_last_event = fields.Char(
        string='Stripe Last Event',
        copy=False,
    )
    stripe_last_event_at = fields.Datetime(
        string='Stripe Last Event At',
        copy=False,
    )
    stripe_grace_until = fields.Date(
        string='Stripe Grace Until',
        copy=False,
    )
    stripe_coupon_code = fields.Char(
        string='Stripe Coupon Code',
        copy=False,
    )
    stripe_trial_end = fields.Date(
        string='Stripe Trial End',
        copy=False,
    )

    subscription_suspended = fields.Boolean(
        string="Suscripción suspendida por impago",
        default=False,
        tracking=True,
        copy=False,
        help=(
            "Se activa automáticamente cuando hay cuotas vencidas sin pagar "
            "tras el período de gracia configurado. Se desactiva cuando "
            "todas las cuotas vencidas están pagadas."
        ),
    )

    # --- Stripe mode ---
    irg_subscription_stripe_mode = fields.Selection(
        selection=[
            ('tokenized_charge', 'Tokenized charge'),
            ('payment_link_fallback', 'Payment link fallback'),
            ('stripe_subscription_real', 'Stripe subscription real'),
        ],
        string='IRG Stripe Mode',
        default='tokenized_charge',
        copy=False,
        tracking=True,
    )

    # --- Payment link (send_invoice) fields ---
    stripe_hosted_invoice_url = fields.Char(
        string='Stripe Payment Link',
        copy=False,
        readonly=True,
        help="URL de la página de pago hosted por Stripe para la factura actual.",
    )
    stripe_invoice_id = fields.Char(
        string='Stripe Invoice ID',
        copy=False,
        readonly=True,
        help="ID de la última factura Stripe pendiente (in_xxx).",
    )
    stripe_last_reminder_sent = fields.Datetime(
        string='Último recordatorio enviado',
        copy=False,
        readonly=True,
    )
    stripe_reminder_count = fields.Integer(
        string='Recordatorios enviados',
        default=0,
        copy=False,
        readonly=True,
    )

    def _irg_mark_stripe_event(self, event_name, state=None, grace_until=False, clear_grace=False):
        now = fields.Datetime.now()
        for order in self:
            vals = {
                'stripe_last_event': event_name,
                'stripe_last_event_at': now,
            }
            if state:
                vals['stripe_subscription_state'] = state
            if clear_grace:
                vals['stripe_grace_until'] = False
            elif grace_until:
                vals['stripe_grace_until'] = grace_until
            order.sudo().write(vals)

    def action_irg_pause_subscription(self):
        api = self.env['irg.stripe.api']
        for order in self.filtered(lambda so: so.is_subscription):
            # Sync with Stripe if native subscription exists
            if order.stripe_subscription_ref and order.stripe_subscription_ref.startswith('sub_'):
                api._pause_stripe_subscription(order.stripe_subscription_ref)
            order.sudo().write({
                'stripe_subscription_state': 'paused',
                'subscription_suspended': True,
            })
            order.message_post(
                body="⏸️ <b>Suscripción pausada manualmente.</b>",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_irg_resume_subscription(self):
        api = self.env['irg.stripe.api']
        for order in self.filtered(lambda so: so.is_subscription):
            # Sync with Stripe if native subscription exists
            if order.stripe_subscription_ref and order.stripe_subscription_ref.startswith('sub_'):
                api._resume_stripe_subscription(order.stripe_subscription_ref)
            order.sudo().write({
                'stripe_subscription_state': 'active',
                'subscription_suspended': False,
                'stripe_grace_until': False,
            })
            order.message_post(
                body="▶️ <b>Suscripción reactivada manualmente.</b>",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_irg_cancel_subscription(self):
        api = self.env['irg.stripe.api']
        for order in self.filtered(lambda so: so.is_subscription):
            # Sync with Stripe if native subscription exists
            if order.stripe_subscription_ref and order.stripe_subscription_ref.startswith('sub_'):
                api._cancel_stripe_subscription(order.stripe_subscription_ref)
            order.sudo().write({
                'stripe_subscription_state': 'canceled',
                'subscription_suspended': True,
                'to_renew': False,
            })
            order.message_post(
                body="🛑 <b>Suscripción cancelada manualmente.</b>",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
        return True

    @api.model
    def _cron_apply_stripe_grace_period(self):
        today = fields.Date.today()
        stage_suspend = self.env['sale.order.stage'].sudo().search(
            [('name', 'ilike', 'Suspendida')], limit=1
        )
        candidates = self.sudo().search([
            ('is_subscription', '=', True),
            ('stripe_subscription_state', '=', 'past_due'),
            ('subscription_suspended', '=', False),
            ('stripe_grace_until', '!=', False),
            ('stripe_grace_until', '<', today),
        ])

        for order in candidates:
            vals = {
                'subscription_suspended': True,
                'stripe_subscription_state': 'paused',
            }
            if stage_suspend:
                vals['stage_id'] = stage_suspend.id
            order.write(vals)
            order.message_post(
                body=(
                    "⚠️ <b>Suscripción pausada por fin de período de gracia Stripe.</b><br/>"
                    "Fecha límite de gracia: <b>%s</b>" % order.stripe_grace_until
                ),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    # ------------------------------------------------------------------
    #  CRON: Suspender suscripciones con cuotas vencidas
    # ------------------------------------------------------------------
    @api.model
    def _cron_check_overdue_subscriptions(self):
        """
        Cron diario: busca suscripciones activas con cuotas vencidas
        más allá del período de gracia y las marca como suspendidas.

        NO MODIFICA sale.subscription.schedule.
        Solo escribe en sale.order.subscription_suspended y stage_id.
        """
        grace_days = int(
            self.env['ir.config_parameter']
            .sudo()
            .get_param('irg_stripe.overdue_grace_days', '15')
        )
        cutoff_date = fields.Date.today() - timedelta(days=grace_days)

        # Buscar suscripciones activas NO suspendidas
        candidates = self.sudo().search([
            ('is_subscription', '=', True),
            ('state', 'in', ('sale', 'done')),
            ('subscription_suspended', '=', False),
        ])

        suspension_stage = self.env['sale.order.stage'].sudo().search(
            [('name', 'ilike', 'Suspendida')], limit=1
        )

        suspended_count = 0

        for order in candidates:
            # Verificar si tiene cuotas vencidas sin pagar
            overdue_lines = order.subscription_schedule.filtered(
                lambda s: (
                    s.date_due
                    and s.date_due < cutoff_date
                    and s.payment_state == 'not_paid'
                )
            )
            if not overdue_lines:
                continue

            overdue_count = len(overdue_lines)
            total_overdue = sum(
                overdue_lines.mapped('amount_recurring_taxinc')
            )

            vals = {'subscription_suspended': True}
            if suspension_stage:
                vals['stage_id'] = suspension_stage.id
            if order.stripe_subscription_state not in ('paused', 'canceled'):
                vals['stripe_subscription_state'] = 'past_due'
            order.write(vals)

            # Notificación interna en el chatter
            order.message_post(
                body=(
                    "⚠️ <b>Suscripción suspendida automáticamente.</b><br/>"
                    "Cuotas vencidas: <b>%d</b><br/>"
                    "Total impagado: <b>%.2f %s</b><br/>"
                    "Período de gracia superado: <b>%d días</b>"
                    % (
                        overdue_count,
                        total_overdue,
                        order.currency_id.name,
                        grace_days,
                    )
                ),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

            suspended_count += 1
            _logger.warning(
                "IRG Overdue: Suscripción %s suspendida — "
                "%d cuota(s) vencida(s), total: %.2f %s",
                order.name,
                overdue_count,
                total_overdue,
                order.currency_id.name,
            )

        _logger.info(
            "IRG Cron overdue: %d suscripciones suspendidas de %d candidatas",
            suspended_count,
            len(candidates),
        )

    # ------------------------------------------------------------------
    #  CRON: Reactivar suscripciones que ya no tienen deuda vencida
    # ------------------------------------------------------------------
    @api.model
    def _cron_reactivate_subscriptions(self):
        """
        Cron diario: busca suscripciones suspendidas cuyas cuotas vencidas
        ya están pagadas y las reactiva automáticamente.

        NO MODIFICA sale.subscription.schedule.
        Solo escribe en sale.order.subscription_suspended y stage_id.
        """
        suspended = self.sudo().search([
            ('subscription_suspended', '=', True),
        ])

        progress_stage = self.env['sale.order.stage'].sudo().search(
            [('name', 'ilike', 'En curso')], limit=1
        )

        reactivated_count = 0

        for order in suspended:
            still_overdue = order.subscription_schedule.filtered(
                lambda s: (
                    s.date_due
                    and s.date_due < fields.Date.today()
                    and s.payment_state == 'not_paid'
                )
            )
            if still_overdue:
                continue  # Aún tiene deuda vencida

            vals = {'subscription_suspended': False}
            if progress_stage:
                vals['stage_id'] = progress_stage.id
            if order.stripe_subscription_state != 'canceled':
                vals['stripe_subscription_state'] = 'active'
                vals['stripe_grace_until'] = False
            order.write(vals)

            order.message_post(
                body=(
                    "✅ <b>Suscripción reactivada.</b><br/>"
                    "Todas las cuotas vencidas han sido pagadas."
                ),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

            reactivated_count += 1
            _logger.info(
                "IRG Reactivate: Suscripción %s reactivada", order.name
            )

        _logger.info(
            "IRG Cron reactivate: %d suscripciones reactivadas de %d suspendidas",
            reactivated_count,
            len(suspended),
        )

    # ------------------------------------------------------------------
    #  CRON: Enviar recordatorios de pago con enlace Stripe
    # ------------------------------------------------------------------
    @api.model
    def _cron_send_payment_link_reminders(self):
        """
        Cron diario: envía recordatorios por email a suscripciones en modo
        ``payment_link_fallback`` que tienen una factura Stripe abierta
        con ``hosted_invoice_url``. Se envía un recordatorio cada N días
        (configurable, default 3).
        """
        reminder_interval = int(
            self.env['ir.config_parameter']
            .sudo()
            .get_param('irg_stripe.payment_link_reminder_interval', '3')
        )
        now = fields.Datetime.now()
        cutoff = now - timedelta(days=reminder_interval)

        candidates = self.sudo().search([
            ('is_subscription', '=', True),
            ('irg_subscription_stripe_mode', '=', 'payment_link_fallback'),
            ('stripe_hosted_invoice_url', '!=', False),
            ('stripe_subscription_state', 'in', ('active', 'past_due')),
            ('subscription_suspended', '=', False),
            '|',
            ('stripe_last_reminder_sent', '=', False),
            ('stripe_last_reminder_sent', '<=', cutoff),
        ])

        template = self.env.ref(
            'irg_payment_stripe_recurring.mail_template_payment_link_reminder',
            raise_if_not_found=False,
        )
        sent_count = 0

        for order in candidates:
            if not order.stripe_hosted_invoice_url:
                continue

            if template:
                template.sudo().send_mail(order.id, force_send=True)

            order.sudo().write({
                'stripe_last_reminder_sent': now,
                'stripe_reminder_count': order.stripe_reminder_count + 1,
            })
            order.message_post(
                body=(
                    "📧 <b>Recordatorio de pago #%d enviado.</b><br/>"
                    "Enlace: <a href='%s'>Pagar factura</a>"
                    % (
                        order.stripe_reminder_count,
                        order.stripe_hosted_invoice_url,
                    )
                ),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            sent_count += 1

        _logger.info(
            "IRG Cron reminders: %d recordatorios enviados de %d candidatas",
            sent_count,
            len(candidates),
        )

    def action_irg_send_payment_reminder(self):
        """Manual button to send a payment link reminder immediately."""
        self.ensure_one()
        if not self.stripe_hosted_invoice_url:
            from odoo.exceptions import UserError
            raise UserError(
                'No hay enlace de pago Stripe disponible para esta suscripción.'
            )

        template = self.env.ref(
            'irg_payment_stripe_recurring.mail_template_payment_link_reminder',
            raise_if_not_found=False,
        )
        if template:
            template.sudo().send_mail(self.id, force_send=True)

        now = fields.Datetime.now()
        self.sudo().write({
            'stripe_last_reminder_sent': now,
            'stripe_reminder_count': self.stripe_reminder_count + 1,
        })
        self.message_post(
            body=(
                "📧 <b>Recordatorio de pago manual #%d enviado.</b><br/>"
                "Enlace: <a href='%s'>Pagar factura</a>"
                % (
                    self.stripe_reminder_count,
                    self.stripe_hosted_invoice_url,
                )
            ),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return True
