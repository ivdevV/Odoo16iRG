# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _is_customer_invoice_to_remind(self):
        self.ensure_one()
        return (
            self.move_type == 'out_invoice'
            and self.state == 'posted'
            and self.payment_state in ('not_paid')
            and self.invoice_date_due
            and self.partner_id.email

        )

    def _get_portal_link(self):
        self.ensure_one()
        try:
            return self.sudo()._get_portal_url()
        except Exception:
            return False

    def _send_reminder_email(self, tmp_xmlid, extra_context=None):
        self.ensure_one()
        if not self._is_customer_invoice_to_remind():
            return False
        
        template = self.env.ref(tmp_xmlid, raise_if_not_found=False)
        if not template:
            return False
        
        portal_link = self._get_portal_link()

        ctx = {
            'default_model': 'account.move',
            'default_res_id': self.id,
            'force_send': True,
            'invoice_due_date': self.invoice_date_due,
            'amount_total': self.amount_total,
            'amount_residual': self.amount_residual,
            'portal_link': portal_link or '',
        }

        if extra_context:
            ctx.update(extra_context)

        template.with_context(ctx).send_mail(self.id, force_send=True)
        return True

    def cron_invoice_due_reminders(self):
        today = fields.Date.context_today(self)
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid']),
            ('invoice_date_due', '!=', False),
            ('partner_id.email', '!=', False),
        ]

        invoices = self.search(domain)
        batch_size = 100

        # Procesar en bloques de 100
        for start in range(0, len(invoices), batch_size):
            batch = invoices[start:start + batch_size]

            for inv in batch:
                if not inv._is_customer_invoice_to_remind():
                    continue

                delta = (inv.invoice_date_due - today).days
                if delta == 7:
                    inv._send_reminder_email('isep_invoice_due_reminders.email_template_invoice_due_7_days')
                    continue

                if delta == 2:
                    inv._send_reminder_email('isep_invoice_due_reminders.email_template_invoice_due_2_3_days')
                    continue

                if delta == 0:
                    inv._send_reminder_email('isep_invoice_due_reminders.email_template_invoice_due_today')
                    continue

                if delta in (-1, -2):
                    inv._send_reminder_email('isep_invoice_due_reminders.email_template_invoice_overdue_1_2_days')
                    continue

        return True



