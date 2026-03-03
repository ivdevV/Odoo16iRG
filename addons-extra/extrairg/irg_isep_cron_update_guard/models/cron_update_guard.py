import logging

from odoo import models

_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _irg_module_operation_in_progress(self):
        return bool(self.env["ir.module.module"].sudo().search_count([
            ("state", "in", ("to install", "to upgrade", "to remove")),
        ]))

    def _create_penalization(self):
        if self._irg_module_operation_in_progress():
            _logger.info("Skipping appointment penalization cron: module operation in progress.")
            return True
        return super()._create_penalization()


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _irg_module_operation_in_progress(self):
        return bool(self.env["ir.module.module"].sudo().search_count([
            ("state", "in", ("to install", "to upgrade", "to remove")),
        ]))

    def _cron_recurring_payment_sale_order(self, meses=None, previsualizar=False, pendiente=False, conpany_all=False):
        if self._irg_module_operation_in_progress():
            _logger.info("Skipping recurring payment cron: module operation in progress.")
            return "Saltado por actualización de módulos en progreso."
        try:
            return super()._cron_recurring_payment_sale_order(
                meses=meses,
                previsualizar=previsualizar,
                pendiente=pendiente,
                conpany_all=conpany_all,
            )
        except AttributeError:
            return "Método de cron no disponible en la cadena de herencia actual."

    def _process_invoice_batch(self, batch, pendiente):
        if self._irg_module_operation_in_progress():
            _logger.info("Skipping segmented payment batch: module operation in progress.")
            return
        try:
            return super()._process_invoice_batch(batch, pendiente)
        except AttributeError:
            return
