# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    irg_stripe_customer_id = fields.Char(
        string="Stripe Customer ID",
        copy=False,
        help="Native Stripe Customer ID (cus_...) used for Stripe Subscriptions.",
    )

    def _irg_ensure_stripe_customer(self, provider=None):
        """
        Return the Stripe Customer ID for this partner, creating one via
        the Stripe API if it does not exist yet.  Persists the ID on
        ``irg_stripe_customer_id``.

        :param provider: optional ``payment.provider`` record to use;
            if not supplied the first active Stripe provider is looked up.
        :returns: Stripe Customer ID string (``cus_...``) or False
        """
        self.ensure_one()
        partner = self.sudo()

        if partner.irg_stripe_customer_id:
            return partner.irg_stripe_customer_id

        if not provider:
            provider = (
                self.env["payment.provider"]
                .sudo()
                .search(
                    [("code", "=", "stripe"), ("state", "in", ("enabled", "test"))],
                    limit=1,
                )
            )
        if not provider:
            _logger.error("IRG Stripe: no active Stripe provider found")
            return False

        payload = {
            "email": partner.email or "",
            "name": partner.name or "",
            "metadata[odoo_partner_id]": str(partner.id),
        }
        result = provider._stripe_make_request("customers", payload=payload)
        customer_id = result.get("id")
        if not customer_id:
            _logger.error(
                "IRG Stripe: failed to create customer for partner %s: %s",
                partner.id,
                result,
            )
            return False

        partner.write({"irg_stripe_customer_id": customer_id})
        _logger.info(
            "IRG Stripe: created customer %s for partner %s (%s)",
            customer_id,
            partner.id,
            partner.name,
        )
        return customer_id
