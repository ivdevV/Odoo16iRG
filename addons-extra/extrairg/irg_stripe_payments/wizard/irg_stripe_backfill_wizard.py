# -*- coding: utf-8 -*-
import calendar
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrgStripeBackfillWizard(models.TransientModel):
    _name = 'irg.stripe.backfill.wizard'
    _description = 'Backfill de pagos Stripe'

    provider_id = fields.Many2one(
        'payment.provider',
        string='Proveedor Stripe',
        required=True,
        domain="[('code', '=', 'stripe')]",
        default=lambda self: self._default_provider_id(),
        help="Obligatorio y explícito a propósito: si hubiera un proveedor de test y "
             "otro de producción activos, o dos cuentas de Stripe, elegir 'el primero' "
             "recorrería la cuenta equivocada sin avisar.",
    )
    date_from = fields.Date(string='Desde', required=True)
    date_to = fields.Date(string='Hasta', required=True, default=fields.Date.context_today)
    mode = fields.Selection(
        [
            ('charges', 'Charges (recomendado)'),
            ('payment_intents', 'PaymentIntents'),
        ],
        string='Endpoint',
        default='charges',
        required=True,
        help="'charges' incluye los cobros legacy y de Terminal sin PaymentIntent, y trae "
             "el importe reembolsado sin una segunda llamada. Usa 'payment_intents' solo "
             "si la cuenta no tiene charges antiguos.",
    )
    resume = fields.Boolean(
        string='Reanudar ejecución previa',
        default=False,
        help="Continúa desde el cursor guardado de una ejecución interrumpida.",
    )
    dry_run = fields.Boolean(
        string='Simulación',
        default=True,
        help="Cuenta lo que traería sin escribir nada en Odoo.",
    )
    result_summary = fields.Text(string='Resultado', readonly=True)

    def _default_provider_id(self):
        return self.env['payment.provider'].sudo().search(
            [('code', '=', 'stripe'), ('state', 'in', ('enabled', 'test'))], limit=1)

    def action_run(self):
        self.ensure_one()
        backfill = self.env['irg.stripe.backfill'].sudo()
        backfill._check_window(self.date_from, self.date_to)

        if self.provider_id.code != 'stripe':
            raise UserError(_("El proveedor seleccionado no es de Stripe."))

        ts_from = calendar.timegm(
            fields.Datetime.to_datetime(f"{self.date_from} 00:00:00").timetuple())
        ts_to = calendar.timegm(
            fields.Datetime.to_datetime(f"{self.date_to} 23:59:59").timetuple())

        summary = backfill._run(
            self.provider_id.sudo(),
            ts_from,
            ts_to,
            mode=self.mode,
            dry_run=self.dry_run,
            resume=self.resume,
            commit=False,
        )

        lines = [
            _("Modo: %s") % (_("simulación") if self.dry_run else _("real")),
            _("Endpoint: %s") % self.mode,
            _("Páginas recorridas: %s") % summary['pages'],
            _("Pagos encontrados en Stripe: %s") % summary['scanned'],
            _("Creados en Odoo: %s") % summary['created'],
            _("Actualizados: %s") % summary['updated'],
            _("Estado: %s") % summary['status'],
        ]
        if summary['status'] == 'partial':
            lines.append(_(
                "Se interrumpió por errores de API. El cursor quedó guardado: vuelve a "
                "lanzar con «Reanudar ejecución previa» marcado."))
        self.result_summary = '\n'.join(lines)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
