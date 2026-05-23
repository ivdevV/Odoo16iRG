# -*- coding: utf-8 -*-
import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal


class IRGSubscriptionCheckoutController(payment_portal.PaymentPortal):
    def _get_stripe_checkout_providers(self, order, amount):
        providers = request.env["payment.provider"].sudo()._get_compatible_providers(
            order.company_id.id,
            order.partner_id.id,
            amount
            if order.irg_subscription_checkout_effective_mode == "initial_payment"
            else 0.0,
            currency_id=order.currency_id.id,
            force_tokenization=True,
            is_validation=order.irg_subscription_checkout_effective_mode == "setup_only",
            sale_order_id=order.id,
        )
        return providers.filtered(lambda provider: provider.code == "stripe")

    def _get_checkout_order(self, order_id, token):
        order = request.env["sale.order"].sudo().browse(order_id)
        if not order.exists() or not order._irg_validate_subscription_checkout_token(token):
            return request.env["sale.order"].sudo(), False
        return order, True

    @http.route(
        "/irg/subscription/checkout/<int:order_id>/<string:token>",
        type="http",
        auth="public",
        website=True,
    )
    def irg_subscription_checkout(self, order_id, token, **kwargs):
        order, valid = self._get_checkout_order(order_id, token)
        if not valid:
            return request.not_found()

        amount, due_date = order._irg_get_first_checkout_amount_and_due_date()
        providers = self._get_stripe_checkout_providers(order, amount)
        if not payment_portal.PaymentPortal._can_partner_pay_in_company(
            order.partner_id, order.company_id
        ):
            providers = request.env["payment.provider"].sudo()

        values = {
            "order": order,
            "amount": amount,
            "due_date": due_date,
            "mode": order.irg_subscription_checkout_effective_mode,
            "providers": providers,
            "tokens": request.env["payment.token"],
            "fees_by_provider": {},
            "show_tokenize_input": self._compute_show_tokenize_input_mapping(
                providers, logged_in=False, sale_order_id=order.id
            ),
            "currency": order.currency_id,
            "partner_id": order.partner_id.id,
            "access_token": token,
            "transaction_route": (
                "/irg/subscription/checkout/transaction/%s/%s" % (order.id, token)
            ),
            "landing_route": order._irg_get_subscription_checkout_url(),
            "reference_prefix": payment_utils.singularize_reference_prefix(prefix="IRG-SUB"),
            "is_subscription": True,
        }
        return request.render(
            "irg_subscription_checkout_link.subscription_checkout_page", values
        )

    @http.route(
        "/irg/subscription/checkout/transaction/<int:order_id>/<string:token>",
        type="json",
        auth="public",
    )
    def irg_subscription_checkout_transaction(self, order_id, token, **kwargs):
        order, valid = self._get_checkout_order(order_id, token)
        if not valid:
            raise werkzeug.exceptions.NotFound()

        amount, _due_date = order._irg_get_first_checkout_amount_and_due_date()
        mode = order.irg_subscription_checkout_effective_mode
        provider = request.env["payment.provider"].sudo().browse(
            kwargs.get("payment_option_id")
        )
        compatible_providers = self._get_stripe_checkout_providers(order, amount)
        if (
            kwargs.get("flow") not in ("redirect", "direct")
            or not provider
            or provider not in compatible_providers
        ):
            raise werkzeug.exceptions.NotFound()

        kwargs.update(partner_id=order.partner_id.id)
        kwargs.pop("custom_create_values", None)

        custom_create_values = {
            "callback_model_id": request.env["ir.model"].sudo()._get_id(order._name),
            "callback_res_id": order.id,
            "callback_method": "_irg_checkout_assign_token_callback",
        }
        if mode == "setup_only":
            kwargs["reference_prefix"] = payment_utils.singularize_reference_prefix(prefix="V")
            kwargs["tokenization_requested"] = True
            tx = self._create_transaction(
                custom_create_values=custom_create_values,
                is_validation=True,
                **kwargs
            )
        else:
            kwargs.update(
                {
                    "amount": amount,
                    "currency_id": order.currency_id.id,
                    "tokenization_requested": True,
                }
            )
            tx = self._create_transaction(
                custom_create_values=custom_create_values,
                is_validation=False,
                **kwargs
            )
        return tx._get_processing_values()
