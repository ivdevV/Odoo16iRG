# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
