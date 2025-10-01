# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _debug_log_lead_count(self, partners):
        Lead = self.env["crm.lead"].with_context(active_test=False)
        user = self.env.user
        uid = user.id
        is_sales_manager = user.has_group("sales_team.group_sale_manager")
        is_sales_user = user.has_group("sales_team.group_sale_salesman")

        for p in partners:
            base_domain = [
                ("partner_id", "child_of", p.commercial_partner_id.id),
                ("type", "=", "opportunity"),
            ]
            domain = list(base_domain)
            if is_sales_user and not is_sales_manager:
                domain.append(("user_id", "in", [uid, False]))

            try:
                count = Lead.search_count(domain)
            except Exception as e:
                _logger.exception(
                    "[CRM Lead Count DEBUG/ERROR] search_count error "
                    "user=%s partner=%s(%s) domain=%s ctx=%s err=%r",
                    uid,
                    p.id,
                    p.display_name,
                    domain,
                    self.env.context,
                    e,
                )
                continue

            acc_ids = Lead.search(domain, limit=50).ids
            all_ids = Lead.sudo().search(domain, limit=200).ids
            denied_ids = [lid for lid in all_ids if lid not in acc_ids]

            _logger.info(
                "[CRM Lead Count DEBUG] user=%s manager=%s sales_user=%s "
                "partner=%s(%s) domain=%s count=%s acc_sample=%s denied_sample=%s",
                uid,
                is_sales_manager,
                is_sales_user,
                p.id,
                p.display_name,
                domain,
                count,
                acc_ids,
                denied_ids[:20],
            )

    def _compute_opportunity_count(self):
        debug = True
        try:
            super(ResPartner, self)._compute_opportunity_count()
        except Exception:
            _logger.exception("[CRM Lead Count] super() raised; entering debug logging")
            try:
                self._debug_log_lead_count(self)
            finally:
                raise

        if debug:
            self._debug_log_lead_count(self)
