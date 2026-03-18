# -*- coding: utf-8 -*-
<<<<<<< HEAD
from odoo import fields, models

=======
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

>>>>>>> 51ba00fd3dd0e1ec35b36b5b3bb53aa8f4ed284a

class ResPartner(models.Model):
    _inherit = "res.partner"

    irg_stripe_customer_id = fields.Char(
        string="Stripe Customer ID",
        copy=False,
<<<<<<< HEAD
        help="Native Stripe Customer ID (cus_...) used for Stripe Subscriptions.",
    )
=======
        help="ID del cliente en Stripe (cus_xxx). Se extrae automáticamente "
             "del token de pago o se crea vía API.",
    )

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    def _irg_get_stripe_provider(self):
        """Return the first active Stripe payment.provider."""
        return (
            self.env["payment.provider"]
            .sudo()
            .search([("code", "=", "stripe"), ("state", "!=", "disabled")], limit=1)
        )

    def _irg_ensure_stripe_customer(self, provider=None):
        """Ensure the partner has a Stripe Customer ID.

        Resolution order:
        1. Already stored in ``irg_stripe_customer_id``.
        2. Extracted from an existing ``payment.token`` linked to this partner.
        3. Created via ``POST /v1/customers``.

        Returns the Stripe Customer ID string or *False* on failure.
        """
        self.ensure_one()

        if self.irg_stripe_customer_id:
            return self.irg_stripe_customer_id

        # Try to get from existing payment tokens
        token = (
            self.env["payment.token"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", self.id),
                    ("provider_code", "=", "stripe"),
                    ("provider_ref", "!=", False),
                ],
                limit=1,
                order="id desc",
            )
        )
        if token and token.provider_ref:
            self.sudo().write({"irg_stripe_customer_id": token.provider_ref})
            _logger.info(
                "IRG Stripe: Customer ID %s extraído del token %s para %s",
                token.provider_ref,
                token.id,
                self.display_name,
            )
            return token.provider_ref

        # Create a new Stripe customer
        if not provider:
            provider = self._irg_get_stripe_provider()
        if not provider:
            _logger.error("IRG Stripe: No se encontró un proveedor Stripe activo.")
            return False

        payload = {
            "name": self.name or "",
            "email": self.email or "",
            "metadata[odoo_partner_id]": str(self.id),
        }
        if self.phone:
            payload["phone"] = self.phone
        if self.vat:
            payload["metadata[vat]"] = self.vat

        try:
            response = provider._stripe_make_request("customers", payload=payload)
        except Exception:
            _logger.exception(
                "IRG Stripe: Error creando customer para partner %s", self.display_name
            )
            return False

        customer_id = response.get("id")
        if not customer_id:
            _logger.error(
                "IRG Stripe: Respuesta sin ID al crear customer para %s: %s",
                self.display_name,
                response,
            )
            return False

        self.sudo().write({"irg_stripe_customer_id": customer_id})
        _logger.info(
            "IRG Stripe: Customer %s creado para %s", customer_id, self.display_name
        )
        return customer_id
>>>>>>> 51ba00fd3dd0e1ec35b36b5b3bb53aa8f4ed284a
