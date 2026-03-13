# -*- coding: utf-8 -*-
import re

from odoo import models


def _get_plan_months(product):
    months = 1
    if not product:
        return months

    plan_ptav = product.product_template_attribute_value_ids.filtered(
        lambda ptav: (ptav.attribute_id.name or '').strip().lower() == 'planes'
    )[:1]
    if not plan_ptav:
        return months

    if getattr(plan_ptav, 'plazo', 0) and plan_ptav.plazo > 0:
        return int(plan_ptav.plazo)

    if plan_ptav.name:
        match = re.search(r'(\d+)\s*mes', plan_ptav.name, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return months


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _isep_get_default_installment_data(self, pricelist=False):
        """Return installment for same default combination behavior as product page.

        Default rule: Online modality (if any) + longest plan.
        """
        self.ensure_one()

        current_pricelist = pricelist
        if not current_pricelist:
            pricelist_id = self.env.context.get('pricelist')
            if pricelist_id:
                current_pricelist = self.env['product.pricelist'].browse(pricelist_id)
        if not current_pricelist:
            current_pricelist = self.env['website'].get_current_website().pricelist_id

        variants = self.product_variant_ids
        if not variants:
            return False, 1

        def _has_online(variant):
            for ptav in variant.product_template_attribute_value_ids:
                attr_name = (ptav.attribute_id.name or '').strip().lower()
                val_name = (ptav.name or '').strip().lower()
                if attr_name == 'modalidad' and 'online' in val_name and 'convenio' not in val_name:
                    return True
            return False

        online_variants = variants.filtered(_has_online)
        candidate_variants = online_variants or variants

        best_installment = False
        best_months = 1
        best_rank = None

        for variant in candidate_variants:
            months = _get_plan_months(variant)
            if months <= 0:
                continue

            variant_price = current_pricelist._get_product_price(variant, 1.0) if current_pricelist else variant.lst_price
            if not variant_price or variant_price <= 0:
                continue

            installment = variant_price / months
            if installment <= 0:
                continue

            rank = (months, -installment)
            if best_rank is None or rank > best_rank:
                best_rank = rank
                best_installment = installment
                best_months = months

        return best_installment, best_months

    def _search_render_results_prices(self, mapping, combination_info):
        """Align search preview price with product default combination logic.

        For subscription products, show the installment computed from the same
        default variant criteria used on product page and listing.
        """
        if not combination_info.get('is_subscription'):
            return super()._search_render_results_prices(mapping, combination_info)

        if not combination_info.get('is_recurrence_possible'):
            return '', 0

        current_pricelist = False
        if mapping and mapping.get('detail') and mapping['detail'].get('pricelist'):
            current_pricelist = mapping['detail']['pricelist']
        if not current_pricelist:
            pricelist_id = self.env.context.get('pricelist')
            if pricelist_id:
                current_pricelist = self.env['product.pricelist'].browse(pricelist_id)
        if not current_pricelist:
            current_pricelist = self.env['website'].get_current_website().pricelist_id

        default_installment_price, default_installment_months = self._isep_get_default_installment_data(
            pricelist=current_pricelist
        )

        if not default_installment_price:
            return super()._search_render_results_prices(mapping, combination_info)

        display_currency = mapping.get('detail', {}).get('display_currency')
        return self.env['ir.ui.view']._render_template(
            'website_sale_subscription.subscription_search_result_price',
            values={
                'currency': display_currency,
                'price': default_installment_price,
                'duration': default_installment_months,
                'unit': 'month',
            }
        ), 0
