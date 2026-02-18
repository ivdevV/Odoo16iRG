# -*- coding: utf-8 -*-
import logging
import re

from odoo import models


_logger = logging.getLogger(__name__)


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


def _non_plan_ptav_ids(product):
    if not product:
        return set()
    return set(product.product_template_attribute_value_ids.filtered(
        lambda ptav: (ptav.attribute_id.name or '').strip().lower() != 'planes'
    ).ids)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _isep_get_min_installment_data(self, pricelist=False, scoped_non_plan_ids=None):
        self.ensure_one()

        current_pricelist = pricelist
        if not current_pricelist:
            pricelist_id = self.env.context.get('pricelist')
            if pricelist_id:
                current_pricelist = self.env['product.pricelist'].browse(pricelist_id)
        if not current_pricelist:
            current_pricelist = self.env['website'].get_current_website().pricelist_id

        variants = self.product_variant_ids
        if scoped_non_plan_ids:
            variants = variants.filtered(lambda variant: _non_plan_ptav_ids(variant) == scoped_non_plan_ids)

        min_installment_price = False
        min_installment_months = 1

        for variant in variants:
            months = _get_plan_months(variant)
            if months <= 0:
                continue

            if self.recurring_invoice and hasattr(self, '_get_first_suitable_pricing_values'):
                pricing_vals = self._get_first_suitable_pricing_values(current_pricelist, variant)
                variant_price = pricing_vals.get('price')
                recurrence_ok = pricing_vals.get('is_recurrence_possible', True)
                if not recurrence_ok:
                    continue
            else:
                variant_price = current_pricelist._get_product_price(variant, 1.0) if current_pricelist else variant.lst_price

            if not variant_price or variant_price <= 0:
                continue

            installment = variant_price / months
            if installment <= 0:
                continue

            if min_installment_price is False or installment < min_installment_price:
                min_installment_price = installment
                min_installment_months = months

        return min_installment_price, min_installment_months

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        selected_product = self.env['product.product'].browse(combination_info.get('product_id')) if combination_info.get('product_id') else self.env['product.product']
        selected_months = _get_plan_months(selected_product)
        combination_info['months'] = selected_months

        current_pricelist = pricelist
        if not current_pricelist:
            pricelist_id = self.env.context.get('pricelist')
            if pricelist_id:
                current_pricelist = self.env['product.pricelist'].browse(pricelist_id)
        if not current_pricelist:
            current_pricelist = self.env['website'].get_current_website().pricelist_id

        selected_non_plan_ids = _non_plan_ptav_ids(selected_product)
        scoped_variants = self.product_variant_ids
        if selected_non_plan_ids:
            scoped_variants = scoped_variants.filtered(
                lambda variant: _non_plan_ptav_ids(variant) == selected_non_plan_ids
            )

        min_installment_price, min_installment_months = self._isep_get_min_installment_data(
            pricelist=current_pricelist,
            scoped_non_plan_ids=selected_non_plan_ids,
        )

        if min_installment_price is not False:
            combination_info['min_installment_price'] = min_installment_price
            combination_info['min_installment_months'] = min_installment_months

        _logger.info(
            "ISEP Monthly Price Debug: Product=%s selected_months=%s selected_price=%s min_installment=%s min_months=%s",
            combination_info.get('product_id'),
            selected_months,
            combination_info.get('price'),
            combination_info.get('min_installment_price'),
            combination_info.get('min_installment_months'),
        )
        
        return combination_info

    def _search_render_results_prices(self, mapping, combination_info):
        if not combination_info.get('is_subscription'):
            return super()._search_render_results_prices(mapping, combination_info)

        min_installment_price, min_installment_months = self._isep_get_min_installment_data(
            pricelist=self.env['website'].get_current_website().get_current_pricelist(),
        )

        if not min_installment_price:
            return super()._search_render_results_prices(mapping, combination_info)

        return self.env['ir.ui.view']._render_template(
            'website_sale_subscription.subscription_search_result_price',
            values={
                'currency': mapping['detail']['display_currency'],
                'price': min_installment_price,
                'duration': min_installment_months,
                'unit': 'month',
            }
        ), 0

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductProduct, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)
        
        target_product_id = product_id or (self.id if self else False)

        if target_product_id:
            product = self.env['product.product'].browse(target_product_id)
            months = _get_plan_months(product)
            combination_info['months'] = months

            current_pricelist = pricelist
            if not current_pricelist:
                pricelist_id = self.env.context.get('pricelist')
                if pricelist_id:
                    current_pricelist = self.env['product.pricelist'].browse(pricelist_id)
            if not current_pricelist:
                current_pricelist = self.env['website'].get_current_website().pricelist_id

            selected_non_plan_ids = _non_plan_ptav_ids(product)
            scoped_variants = product.product_tmpl_id.product_variant_ids
            if selected_non_plan_ids:
                scoped_variants = scoped_variants.filtered(
                    lambda variant: _non_plan_ptav_ids(variant) == selected_non_plan_ids
                )

            min_installment_price = False
            min_installment_months = 1
            for variant in scoped_variants:
                variant_months = _get_plan_months(variant)
                if variant_months <= 0:
                    continue

                variant_price = current_pricelist._get_product_price(variant, 1.0) if current_pricelist else variant.lst_price
                installment = variant_price / variant_months
                if installment <= 0:
                    continue

                if min_installment_price is False or installment < min_installment_price:
                    min_installment_price = installment
                    min_installment_months = variant_months

            if min_installment_price is not False:
                combination_info['min_installment_price'] = min_installment_price
                combination_info['min_installment_months'] = min_installment_months

        else:
            months = 1

        combination_info['months'] = months
        return combination_info
