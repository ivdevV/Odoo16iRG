# -*- coding: utf-8 -*-
import logging
import secrets

from odoo import _, api, fields, models
from odoo.fields import Command

_logger = logging.getLogger(__name__)


def _irg_mask_log_value(value, keep=4):
    if not value:
        return "-"
    value = str(value)
    if len(value) <= keep:
        return "*" * len(value)
    return "...%s" % value[-keep:]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    irg_subscription_checkout_token = fields.Char(
        string="IRG Subscription Checkout Token",
        copy=False,
        readonly=True,
    )
    irg_subscription_checkout_url = fields.Char(
        string="IRG Subscription Checkout URL",
        compute="_compute_irg_subscription_checkout_url",
        readonly=True,
    )
    irg_subscription_checkout_mode = fields.Selection(
        [
            ("auto", "Auto"),
            ("initial_payment", "Initial payment"),
            ("setup_only", "Setup only"),
        ],
        string="IRG Subscription Checkout Mode",
        default="auto",
        copy=False,
    )
    irg_subscription_checkout_effective_mode = fields.Selection(
        [
            ("initial_payment", "Initial payment"),
            ("setup_only", "Setup only"),
        ],
        string="IRG Effective Checkout Mode",
        compute="_compute_irg_subscription_checkout_effective_mode",
        readonly=True,
    )
    irg_pending_payment_transaction_id = fields.Many2one(
        "payment.transaction",
        string="IRG Pending Checkout Transaction",
        copy=False,
        readonly=True,
    )
    irg_pending_payment_token_id = fields.Many2one(
        "payment.token",
        string="IRG Pending Checkout Token",
        copy=False,
        readonly=True,
    )
    irg_checkout_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("paid_pending_confirmation", "Paid pending confirmation"),
            ("tokenized_pending_confirmation", "Tokenized pending confirmation"),
            ("consumed", "Consumed"),
            ("expired", "Expired"),
            ("error", "Error"),
        ],
        string="IRG Checkout State",
        default="draft",
        copy=False,
        tracking=True,
    )

    @api.depends("irg_subscription_checkout_token")
    def _compute_irg_subscription_checkout_url(self):
        for order in self:
            order.irg_subscription_checkout_url = (
                order._irg_get_subscription_checkout_url()
                if order.irg_subscription_checkout_token
                else False
            )

    @api.depends(
        "irg_subscription_checkout_mode",
        "subscription_schedule.date_due",
        "payment_term_id",
        "start_date",
        "date_order",
    )
    def _compute_irg_subscription_checkout_effective_mode(self):
        today = fields.Date.today()
        for order in self:
            if order.irg_subscription_checkout_mode in ("initial_payment", "setup_only"):
                order.irg_subscription_checkout_effective_mode = (
                    order.irg_subscription_checkout_mode
                )
                continue
            _amount, due_date = order._irg_get_first_checkout_amount_and_due_date()
            order.irg_subscription_checkout_effective_mode = (
                "initial_payment" if due_date <= today else "setup_only"
            )

    def _irg_get_subscription_checkout_url(self):
        self.ensure_one()
        if not self.irg_subscription_checkout_token:
            return False
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        return "%s/irg/subscription/checkout/%s/%s" % (
            base_url.rstrip("/"),
            self.id,
            self.irg_subscription_checkout_token,
        )

    def _irg_generate_subscription_checkout_token(self):
        self.ensure_one()
        if not self.irg_subscription_checkout_token:
            self.sudo().write(
                {"irg_subscription_checkout_token": secrets.token_urlsafe(32)}
            )
        return self.irg_subscription_checkout_token

    def action_irg_generate_subscription_checkout_link(self):
        for order in self:
            order._irg_generate_subscription_checkout_token()
            vals = {}
            if order.irg_checkout_state == "draft":
                vals["irg_checkout_state"] = "sent"
            if vals:
                order.sudo().write(vals)
            if hasattr(order, "_portal_ensure_token"):
                order._portal_ensure_token()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Subscription checkout link generated"),
                "message": _("The public checkout link is available on the order."),
                "sticky": False,
                "type": "success",
            },
        }

    def action_irg_send_subscription_checkout_link(self):
        template = self.env.ref(
            "irg_subscription_checkout_link.mail_template_subscription_checkout_link",
            raise_if_not_found=False,
        )
        for order in self:
            order.action_irg_generate_subscription_checkout_link()
            if template:
                template.sudo().send_mail(order.id, force_send=True)
        return True

    def _irg_get_first_checkout_amount_and_due_date(self):
        self.ensure_one()
        today = fields.Date.today()
        schedules = self.subscription_schedule.sorted("date_due")
        if schedules:
            unpaid = schedules.filtered(lambda s: s.payment_state == "not_paid")
            schedule = (unpaid or schedules)[:1]
            amount = schedule.amount_recurring_taxinc or self.amount_total
            due_date = schedule.date_due or schedule.date_schedule or today
            return amount, due_date

        ref_date = self.start_date or fields.Date.to_date(self.date_order) or today
        if self.payment_term_id:
            try:
                terms = self.payment_term_id._compute_terms(
                    date_ref=ref_date,
                    currency=self.currency_id,
                    company=self.company_id,
                    tax_amount=self.amount_tax,
                    tax_amount_currency=self.amount_tax,
                    sign=1,
                    untaxed_amount=self.amount_untaxed,
                    untaxed_amount_currency=self.amount_untaxed,
                    cash_rounding=None,
                )
                if terms:
                    return terms[0].get("company_amount") or terms[0].get("foreign_amount") or self.amount_total, terms[0].get("date") or ref_date
            except Exception:
                _logger.warning(
                    "IRG checkout: could not compute payment terms for %s",
                    self.name,
                    exc_info=True,
                )
        return self.amount_total, ref_date

    def _irg_validate_subscription_checkout_token(self, token):
        self.ensure_one()
        has_pending = bool(
            self.irg_pending_payment_transaction_id
            or self.irg_pending_payment_token_id
        )
        return bool(
            token
            and self.irg_subscription_checkout_token
            and secrets.compare_digest(self.irg_subscription_checkout_token, token)
            and self.irg_checkout_state in ("draft", "sent")
            and not has_pending
            and self.state in ("draft", "sent", "sale", "done")
        )

    def _irg_checkout_transaction_is_acceptable(self, tx):
        self.ensure_one()
        if not tx or not getattr(tx, "renewal_allowed", False):
            return False
        if tx.partner_id.commercial_partner_id != self.partner_id.commercial_partner_id:
            return False
        if tx.company_id and tx.company_id != self.company_id:
            return False
        if self.irg_pending_payment_transaction_id or self.irg_pending_payment_token_id:
            return False

        token = tx.token_id
        if not token:
            return False
        if tx.provider_code != "stripe" or token.provider_id.code != "stripe":
            return False
        if not getattr(token, "stripe_payment_method", False):
            return False
        if token.partner_id.commercial_partner_id != self.partner_id.commercial_partner_id:
            return False
        if token.company_id and token.company_id != self.company_id:
            return False
        if token.provider_id != tx.provider_id:
            return False

        mode = self.irg_subscription_checkout_effective_mode
        if mode == "initial_payment":
            amount, _due_date = self._irg_get_first_checkout_amount_and_due_date()
            return abs(tx.amount - amount) < 0.01
        return tx.operation == "validation"

    def _irg_record_checkout_transaction(self, tx):
        for order in self:
            if not order._irg_checkout_transaction_is_acceptable(tx):
                return False
            vals = {}
            tx_id = getattr(tx, "id", False)
            token = getattr(tx, "token_id", False)
            token_id = getattr(token, "id", False) if token else False
            if tx_id:
                vals["irg_pending_payment_transaction_id"] = tx_id
            if token_id:
                vals["irg_pending_payment_token_id"] = token_id
            vals["irg_checkout_state"] = (
                "tokenized_pending_confirmation"
                if order.irg_subscription_checkout_effective_mode == "setup_only"
                else "paid_pending_confirmation"
            )
            order.sudo().write(vals)
        return True

    def _irg_checkout_assign_token_callback(self, tx):
        self.ensure_one()
        recorded = self._irg_record_checkout_transaction(tx)
        if not recorded:
            _logger.warning(
                "IRG checkout: rejected callback persistence for order %s (tx=%s, token=%s)",
                self.name,
                getattr(tx, "reference", False) or getattr(tx, "id", False) or "-",
                _irg_mask_log_value(
                    getattr(getattr(tx, "token_id", False), "provider_ref", False)
                ),
            )
        return recorded

    def _irg_has_stripe_subscription(self):
        self.ensure_one()
        existing_sub = getattr(self, "stripe_subscription_id", False)
        existing_sub_id = False
        if existing_sub:
            if isinstance(existing_sub, models.BaseModel):
                existing_sub_id = getattr(existing_sub, "stripe_id", False)
            else:
                existing_sub_id = existing_sub
        if not existing_sub_id:
            existing_sub_id = getattr(self, "stripe_subscription_ref", False)
        return bool(existing_sub_id and isinstance(existing_sub_id, str) and existing_sub_id.startswith("sub_"))

    def _irg_consume_pending_subscription_checkout(self):
        for order in self:
            had_pending = bool(
                order.irg_pending_payment_token_id
                or order.irg_pending_payment_transaction_id
            )
            if order.irg_pending_payment_token_id and not order.payment_token_id:
                order.sudo().write(
                    {"payment_token_id": order.irg_pending_payment_token_id.id}
                )
            if (
                order.irg_pending_payment_transaction_id
                and order not in order.irg_pending_payment_transaction_id.sale_order_ids
            ):
                order.irg_pending_payment_transaction_id.sudo().write(
                    {"sale_order_ids": [Command.link(order.id)]}
                )
            if (
                order.state in ("sale", "done")
                and getattr(order, "irg_subscription_stripe_mode", False)
                in ("stripe_subscription_real", "payment_link_fallback")
                and not order._irg_has_stripe_subscription()
            ):
                try:
                    sub_id = order._irg_create_stripe_subscription()
                    if sub_id:
                        vals = {}
                        if "stripe_subscription_id" in order._fields:
                            vals["stripe_subscription_id"] = sub_id
                        if "stripe_subscription_ref" in order._fields:
                            vals["stripe_subscription_ref"] = sub_id
                        if vals:
                            order.sudo().write(vals)
                except Exception:
                    _logger.exception(
                        "IRG checkout: could not create Stripe subscription for %s",
                        order.name,
                    )
                    order.sudo().write({"irg_checkout_state": "error"})
                    continue
            if had_pending and order.irg_checkout_state != "consumed":
                order.sudo().write({"irg_checkout_state": "consumed"})
        return True
