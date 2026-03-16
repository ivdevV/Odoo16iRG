import logging

from odoo import _, api, fields, models
from odoo.osv import expression


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    irg_subscription_billing_strategy = fields.Selection(
        selection=[
            ("legacy_installments", "Legacy installments"),
            ("single_invoice_schedule", "Single invoice + payment schedule"),
        ],
        string="IRG Billing Strategy",
        default="legacy_installments",
        copy=False,
        tracking=True,
    )
    irg_subscription_stripe_mode = fields.Selection(
        selection=[
            ("tokenized_charge", "Tokenized charge"),
            ("payment_link_fallback", "Payment link fallback"),
            ("stripe_subscription_real", "Stripe subscription real"),
        ],
        string="IRG Stripe Mode",
        default="tokenized_charge",
        copy=False,
        tracking=True,
    )
    irg_payment_link_fallback_enabled = fields.Boolean(
        string="IRG Payment Link Fallback",
        default=True,
        copy=False,
        tracking=True,
    )
    irg_adjustment_ids = fields.One2many(
        "irg.subscription.adjustment",
        "sale_order_id",
        string="IRG Temporary Adjustments",
    )
    irg_adjustment_count = fields.Integer(
        string="IRG Adjustment Count",
        compute="_compute_irg_adjustment_count",
    )
    irg_single_invoice_move_id = fields.Many2one(
        "account.move",
        string="IRG Single Invoice",
        copy=False,
        readonly=True,
    )
    irg_single_invoice_state = fields.Selection(
        related="irg_single_invoice_move_id.state",
        string="IRG Single Invoice State",
        readonly=True,
    )
    irg_single_invoice_payment_state = fields.Selection(
        related="irg_single_invoice_move_id.payment_state",
        string="IRG Single Invoice Payment State",
        readonly=True,
    )
    irg_single_invoice_linked_count = fields.Integer(
        string="Linked Installments",
        compute="_compute_irg_single_invoice_linked_count",
    )
    irg_stripe_bridge_state = fields.Selection(
        selection=[
            ("not_required", "Not required"),
            ("tokenized_charge", "Tokenized charge"),
            ("payment_link_fallback", "Payment link fallback"),
            ("pending_real_subscription", "Pending Stripe subscription"),
        ],
        string="IRG Stripe Bridge State",
        default="not_required",
        copy=False,
        tracking=True,
    )

    def _compute_irg_adjustment_count(self):
        for order in self:
            order.irg_adjustment_count = len(order.irg_adjustment_ids)

    def _compute_irg_single_invoice_linked_count(self):
        for order in self:
            order.irg_single_invoice_linked_count = len(
                order.subscription_schedule.filtered("move_line_id")
            )

    def _irg_subscription_runtime_lines(self):
        self.ensure_one()
        return self.order_line.filtered(
            lambda line: not line.display_type and line.product_template_id.recurring_invoice
        )

    def _irg_get_subscription_runtime_config(self):
        self.ensure_one()
        strategy = "legacy_installments"
        stripe_mode = "tokenized_charge"
        payment_link_fallback = True

        for template in self._irg_subscription_runtime_lines().mapped("product_template_id"):
            if template.irg_subscription_billing_strategy == "single_invoice_schedule":
                strategy = "single_invoice_schedule"

            if template.irg_subscription_stripe_mode == "stripe_subscription_real":
                stripe_mode = "stripe_subscription_real"
            elif (
                template.irg_subscription_stripe_mode == "payment_link_fallback"
                and stripe_mode != "stripe_subscription_real"
            ):
                stripe_mode = "payment_link_fallback"

            payment_link_fallback = payment_link_fallback or template.irg_payment_link_fallback_enabled

        return {
            "irg_subscription_billing_strategy": strategy,
            "irg_subscription_stripe_mode": stripe_mode,
            "irg_payment_link_fallback_enabled": payment_link_fallback,
        }

    def _irg_sync_subscription_configuration_from_lines(self):
        for order in self:
            if not order._irg_subscription_runtime_lines():
                continue
            order.update(order._irg_get_subscription_runtime_config())

    def _irg_should_use_single_invoice_strategy(self):
        self.ensure_one()
        return self.irg_subscription_billing_strategy == "single_invoice_schedule"

    def action_open_irg_single_invoice(self):
        self.ensure_one()
        if not self.irg_single_invoice_move_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("IRG Single Invoice"),
            "res_model": "account.move",
            "res_id": self.irg_single_invoice_move_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        self.ensure_one()
        if self._irg_should_use_single_invoice_strategy():
            invoice_vals.update(
                {
                    "order_subscription_id": self.id,
                    "irg_single_subscription_invoice": True,
                    "invoice_date": self.start_date or fields.Date.context_today(self),
                }
            )
            if self.payment_term_id:
                invoice_vals["invoice_payment_term_id"] = self.payment_term_id.id
        return invoice_vals

    def _irg_get_existing_single_invoice(self):
        self.ensure_one()
        if self.irg_single_invoice_move_id and self.irg_single_invoice_move_id.state != "cancel":
            return self.irg_single_invoice_move_id

        invoices = self.invoice_ids.filtered(
            lambda move: move.move_type == "out_invoice" and move.state != "cancel"
        )
        flagged = invoices.filtered("irg_single_subscription_invoice")
        if flagged:
            return flagged.sorted(lambda move: (move.state != "posted", move.id))[:1]

        for invoice in invoices.sorted(lambda move: move.id):
            if self.currency_id.compare_amounts(invoice.amount_total, self.amount_total) == 0:
                return invoice
        return invoices[:1]

    def _irg_get_receivable_lines_from_invoice(self, invoice):
        self.ensure_one()
        fallback_date = invoice.invoice_date_due or invoice.invoice_date or fields.Date.context_today(self)
        return invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        ).sorted(lambda line: (line.date_maturity or fallback_date, line.id))

    def _irg_get_receivable_line_amount(self, line):
        if line.currency_id and line.move_id.currency_id == line.currency_id:
            return abs(line.amount_currency)
        return abs(line.balance)

    def _irg_sync_stripe_bridge_state(self):
        for order in self:
            if not order._irg_should_use_single_invoice_strategy():
                order.irg_stripe_bridge_state = "not_required"
                continue

            if order.irg_subscription_stripe_mode == "stripe_subscription_real":
                values = {
                    "irg_stripe_bridge_state": "pending_real_subscription",
                }
                if order.stripe_subscription_state == "draft":
                    values["stripe_subscription_state"] = "draft"
                order.sudo().write(values)
            elif order.irg_subscription_stripe_mode == "payment_link_fallback":
                order.irg_stripe_bridge_state = "payment_link_fallback"
            else:
                order.irg_stripe_bridge_state = "tokenized_charge"

    def _irg_register_single_invoice(self, invoice):
        self.ensure_one()
        if not invoice:
            return False

        invoice.sudo().write(
            {
                "irg_single_subscription_invoice": True,
                "order_subscription_id": self.id,
            }
        )
        self.sudo().write({"irg_single_invoice_move_id": invoice.id})

        receivable_lines = self._irg_get_receivable_lines_from_invoice(invoice)
        schedules = self.subscription_schedule.sorted("date_due")
        linked_count = min(len(schedules), len(receivable_lines))

        for index in range(linked_count):
            schedule = schedules[index]
            line = receivable_lines[index]
            amount = self.currency_id.round(self._irg_get_receivable_line_amount(line))
            due_date = line.date_maturity or invoice.invoice_date_due or invoice.invoice_date
            schedule_vals = {
                "move_line_id": line.id,
            }
            if due_date:
                schedule_vals.update(
                    {
                        "date_due": due_date,
                        "date_schedule": due_date,
                    }
                )
            if amount:
                schedule_vals["amount_recurring_taxinc"] = amount
            if not schedule.irg_original_amount_recurring_taxinc:
                schedule_vals["irg_original_amount_recurring_taxinc"] = amount or schedule.amount_recurring_taxinc
            schedule.write(schedule_vals)

        for schedule in schedules[linked_count:]:
            if not schedule.irg_original_amount_recurring_taxinc:
                schedule.irg_original_amount_recurring_taxinc = schedule.amount_recurring_taxinc

        if schedules and len(schedules) != len(receivable_lines):
            _logger.warning(
                "IRG single invoice linking mismatch for %s: %s schedule lines vs %s receivable lines",
                self.name,
                len(schedules),
                len(receivable_lines),
            )

        self._irg_sync_stripe_bridge_state()
        return invoice

    def _irg_ensure_single_invoice(self):
        for order in self.filtered(
            lambda so: so._irg_should_use_single_invoice_strategy() and so.state in ("sale", "done")
        ):
            if order.recurrence_id and not order.subscription_schedule:
                order.create_subscription_schedule()

            invoice = order._irg_get_existing_single_invoice()
            if not invoice:
                invoice = order.sudo()._create_invoices(final=False)
                invoice = order._irg_get_existing_single_invoice() or invoice[:1]

            if not invoice:
                continue
            if invoice.state == "draft":
                invoice.sudo().action_post()
            order._irg_register_single_invoice(invoice)

    def action_open_irg_adjustment_wizard(self):
        self.ensure_one()
        return {
            "name": _("Temporary Installment Adjustment"),
            "type": "ir.actions.act_window",
            "res_model": "irg.subscription.adjustment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_order_id": self.id,
            },
        }

    @api.onchange("order_line")
    def _onchange_irg_sync_subscription_configuration(self):
        self._irg_sync_subscription_configuration_from_lines()

    def _auto_scheduled_order(self):
        result = super()._auto_scheduled_order()
        self._irg_sync_subscription_configuration_from_lines()
        return result

    def create_subscription_schedule(self):
        result = super().create_subscription_schedule()
        for order in self.filtered(lambda so: so._irg_should_use_single_invoice_strategy()):
            for schedule in order.subscription_schedule.filtered(
                lambda line: not line.irg_original_amount_recurring_taxinc
            ):
                schedule.irg_original_amount_recurring_taxinc = schedule.amount_recurring_taxinc
            if order.irg_single_invoice_move_id and order.irg_single_invoice_move_id.state == "posted":
                order._irg_register_single_invoice(order.irg_single_invoice_move_id)
        return result

    def action_confirm(self):
        self._irg_sync_subscription_configuration_from_lines()
        result = super().action_confirm()
        self._irg_sync_subscription_configuration_from_lines()
        self._irg_ensure_single_invoice()
        return result

    def _recurring_invoice_domain_update(self, extra_domain=None):
        strategy_domain = [("irg_subscription_billing_strategy", "!=", "single_invoice_schedule")]
        if extra_domain:
            extra_domain = expression.AND([extra_domain, strategy_domain])
        else:
            extra_domain = strategy_domain
        return super()._recurring_invoice_domain_update(extra_domain=extra_domain)