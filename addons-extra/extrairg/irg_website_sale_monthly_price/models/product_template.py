# -*- coding: utf-8 -*-
import logging
import re

from odoo import models, fields


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


def _get_plan_temporal_price(pricelist, variant, months):
    """Return the total temporal pricing price for the given variant and plan months.

    Looks up product.pricing records filtered by:
    - recurrence_id.unit == 'month'
    - recurrence_id.duration == months  (e.g., 19 for the 19-month plan)
    - pricelist_id matches the given pricelist (or is empty = applies to all)

    Returns the price (currency-converted to pricelist.currency if needed),
    or None if no matching temporal pricing record is found.
    """
    plan_pricings = variant.product_pricing_ids.filtered(
        lambda p: p.recurrence_id.unit == 'month'
        and int(round(p.recurrence_id.duration)) == months
        and (not pricelist or not p.pricelist_id or p.pricelist_id == pricelist)
    )[:1]
    if not plan_pricings:
        return None
    price = plan_pricings[0].price
    if pricelist and pricelist.currency_id != plan_pricings[0].currency_id:
        price = plan_pricings[0].currency_id._convert(
            price, pricelist.currency_id,
            plan_pricings[0].company_id or variant.env.company,
            fields.Date.today(),
        )
    return price


def _variant_installment(pricelist, variant):
    months = _get_plan_months(variant)
    if months <= 1:
        # Contado or single payment — not a split installment plan
        return 0.0, months

    # Use the temporal pricing that precisely matches the plan months.
    # This avoids picking up "Contado" pricing records (ordered first by price ASC)
    # that apply to all variants due to empty product_variant_ids.
    price = _get_plan_temporal_price(pricelist, variant, months)
    if price is None:
        # Fallback: use pricelist price (original behaviour)
        price = pricelist._get_product_price(variant, 1.0) if pricelist else variant.lst_price

    if not price or price <= 0:
        return 0.0, months
    return (price / months), months

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _isep_get_selected_installment_data(self, selected_product, pricelist=False):
        """Return selected installment and a monotonic-capped installment.

        For the same non-plan attributes (modality, campus, etc.), enforce that
        a longer plan does not display a higher monthly installment than a shorter
        one. This only affects display and keeps pricing monotonic for users.
        """
        self.ensure_one()
        if not selected_product:
            return 0.0, 0.0, 1

        current_pricelist = pricelist
        if not current_pricelist:
            pricelist_id = self.env.context.get('pricelist')
            if pricelist_id:
                current_pricelist = self.env['product.pricelist'].browse(pricelist_id)
        if not current_pricelist:
            current_pricelist = self.env['website'].get_current_website().pricelist_id

        selected_installment, selected_months = _variant_installment(current_pricelist, selected_product)
        if not selected_installment or selected_months <= 1:
            return selected_installment, selected_installment, selected_months or 1

        scoped_non_plan_ids = _non_plan_ptav_ids(selected_product)
        scoped_variants = self.product_variant_ids.filtered(
            lambda variant: _non_plan_ptav_ids(variant) == scoped_non_plan_ids
        )

        shorter_installments = []
        for variant in scoped_variants:
            installment, months = _variant_installment(current_pricelist, variant)
            if installment > 0 and 0 < months < selected_months:
                shorter_installments.append(installment)

        capped_installment = selected_installment
        if shorter_installments:
            capped_installment = min(selected_installment, min(shorter_installments))

        return selected_installment, capped_installment, selected_months

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
            installment, months = _variant_installment(current_pricelist, variant)
            if installment <= 0 or months <= 1:
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

        # Override combination_info['price'] with the correct temporal pricing total.
        # Odoo's super() chain (website_sale_subscription) uses _get_first_suitable_pricing
        # which picks the LOWEST priced record (ordered by price ASC). For multi-month
        # plans this returns the "Contado" pricing (lower price, applies to all variants)
        # instead of the "Mensual" temporal pricing that is the actual plan price.
        # We look up the pricing by matching recurrence_id.duration == selected_months.
        if selected_months > 1 and selected_product:
            temporal_price = _get_plan_temporal_price(current_pricelist, selected_product, selected_months)
            if temporal_price is not None and temporal_price > 0:
                combination_info['price'] = temporal_price

        # Compute the global "menor cuota posible" for the whole template (across all variants)
        # — we show the absolute minimum installment available for any valid variant/pricing,
        # not only the variants that match the currently selected non-plan attributes.
        selected_non_plan_ids = _non_plan_ptav_ids(selected_product)

        # Global minimum across all template variants (ignores selected_non_plan_ids)
        global_min_installment_price, global_min_installment_months = self._isep_get_min_installment_data(
            pricelist=current_pricelist,
            scoped_non_plan_ids=None,
        )

        # Keep a scoped minimum for backwards compatibility if needed (not used for UI)
        scoped_min_installment_price, scoped_min_installment_months = (False, 1)
        if selected_non_plan_ids:
            scoped_min_installment_price, scoped_min_installment_months = self._isep_get_min_installment_data(
                pricelist=current_pricelist,
                scoped_non_plan_ids=selected_non_plan_ids,
            )

        # Use the global minimum as the canonical 'min_installment' exposed to the UI
        if global_min_installment_price is not False:
            combination_info['min_installment_price'] = global_min_installment_price
            combination_info['min_installment_months'] = global_min_installment_months
        else:
            # fallback to scoped if global unavailable
            if scoped_min_installment_price is not False:
                combination_info['min_installment_price'] = scoped_min_installment_price
                combination_info['min_installment_months'] = scoped_min_installment_months

        # Keep only raw selected months; do NOT set display_installment_* to avoid
        # server-side normalization. The frontend/templates should compute
        # (combination_info['price'] / combination_info['months']) when needed.
        # This ensures displayed cuota is always variant price divided by months.

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

        if not combination_info.get('is_recurrence_possible'):
            return '', 0

        display_currency = mapping.get('detail', {}).get('display_currency')

        # Prefer the pre-computed global minimum installment (set in _get_combination_info
        # via _isep_get_min_installment_data across all variants). This mirrors what the
        # product page shows when it auto-selects the Online + longest-plan variant
        # (= the lowest per-month installment), regardless of which default combination
        # is passed to the search context (which is often Contado, months=1).
        monthly_price = combination_info.get('min_installment_price')
        duration = combination_info.get('min_installment_months', 1)

        if not monthly_price or duration <= 1:
            # Fallback: compute from the selected combination's price and months.
            duration = (
                combination_info.get('months')
                or combination_info.get('subscription_duration')
                or 1
            )
            total_price = combination_info.get('price') or 0.0
            # If min_installment is not available, try to compute a sensible default
            # using the template default installment logic (same as product page).
            if not monthly_price or duration <= 1:
                template = self[:1]
                default_installment_price, default_installment_months = template._isep_get_default_installment_data(
                    pricelist=current_pricelist
                )
                if default_installment_price and default_installment_months > 1:
                    monthly_price = default_installment_price
                    duration = default_installment_months
                else:
                    if not total_price or duration <= 1:
                        return super()._search_render_results_prices(mapping, combination_info)
                    monthly_price = total_price / duration

        return self.env['ir.ui.view']._render_template(
            'website_sale_subscription.subscription_search_result_price',
            values={
                'currency': display_currency,
                'price': monthly_price,
                'duration': duration,
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

            # Delegate to template-level helper to compute the global minimum across all
            # variants of the product (ensures product page always shows the absolute
            # "menor cuota posible" available for the product).
            min_installment_price, min_installment_months = self.product_tmpl_id._isep_get_min_installment_data(
                pricelist=current_pricelist
            )
            if min_installment_price is not False:
                combination_info['min_installment_price'] = min_installment_price
                combination_info['min_installment_months'] = min_installment_months

            selected_installment, capped_installment, capped_months = self.product_tmpl_id._isep_get_selected_installment_data(
                product,
                pricelist=current_pricelist,
            )
            if capped_installment and capped_months > 1:
                combination_info['selected_installment_price'] = selected_installment
                combination_info['display_installment_price'] = capped_installment
                combination_info['display_installment_months'] = capped_months

        else:
            months = 1

        combination_info['months'] = months
        return combination_info
