# -*- coding: utf-8 -*-
print("ISEP Monthly Price: Loading product_template.py")
from odoo import models, api
import logging

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        months = 1
        # Try to find months from combination (attributes)
        if combination:
            for ptav in combination:
                # Check if attribute name matches 'Planes' (case insensitive just in case)
                if ptav.attribute_id.name and ptav.attribute_id.name.lower() == 'planes':
                    # Check if plazo field exists and has value
                    if hasattr(ptav, 'plazo') and ptav.plazo > 0:
                        months = ptav.plazo
                        break
                    
                    # Fallback: try to parse "X meses" from the name
                    if ptav.name:
                        import re
                        match = re.search(r'(\d+)\s*mes', ptav.name, re.IGNORECASE)
                        if match:
                            months = int(match.group(1))
                            break

        # Fallback to product if combination not explicit (e.g. initial load might have product_id)
        if months == 1 and combination_info.get('product_id'):
            product = self.env['product.product'].browse(combination_info['product_id'])
            for ptav in product.product_template_attribute_value_ids:
                if ptav.attribute_id.name and ptav.attribute_id.name.lower() == 'planes':
                    if hasattr(ptav, 'plazo') and ptav.plazo > 0:
                        months = ptav.plazo
                        break
                    
                    # Fallback: try to parse "X meses" from the name
                    if ptav.name:
                        import re
                        match = re.search(r'(\d+)\s*mes', ptav.name, re.IGNORECASE)
                        if match:
                            months = int(match.group(1))
                            break

        combination_info['months'] = months
        # Add logging to debug
        _logger = logging.getLogger(__name__)
        msg = f"ISEP Monthly Price Debug: Product ID: {combination_info.get('product_id')}, Months: {months}, Price: {combination_info.get('price')}"
        _logger.info(msg)
        print(msg) # Print to stdout to ensure visibility in docker logs
        
        return combination_info

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductProduct, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)
        
        # Reuse logic from template if possible, or just re-implement for safety
        months = 1
        # ... (same logic as above, simplified for product context)
        # Since we are in product.product, self is the product (if singleton)
        # But _get_combination_info might be called on an empty recordset or with product_id
        
        # Actually, let's just rely on the template override if possible, but if website_sale calls product.product directly...
        # website_sale usually calls product_template._get_combination_info
        
        # Let's just inject the months logic here too to be safe
        
        # If product_id is provided in args, use it. If not, use self.id
        target_product_id = product_id or (self.id if self else False)
        
        if target_product_id:
            product = self.env['product.product'].browse(target_product_id)
            for ptav in product.product_template_attribute_value_ids:
                if ptav.attribute_id.name and ptav.attribute_id.name.lower() == 'planes':
                    if hasattr(ptav, 'plazo') and ptav.plazo > 0:
                        months = ptav.plazo
                        break
                    if ptav.name:
                        import re
                        match = re.search(r'(\d+)\s*mes', ptav.name, re.IGNORECASE)
                        if match:
                            months = int(match.group(1))
                            break
        
        combination_info['months'] = months
        return combination_info
