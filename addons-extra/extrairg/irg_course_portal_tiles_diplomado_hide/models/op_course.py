# -*- coding: utf-8 -*-
from odoo import models, fields, api


class OpCourse(models.Model):
    """
    Inherit op.course to add is_diplomado check helper.
    """
    _inherit = 'op.course'

    def is_diplomado(self):
        """
        Check if the course is a Diplomado by verifying:
        - self.course_type_id (code starts with 'DI' or 'D', name contains 'DIPLOMADO' case insensitive)
        - self.product_template_id and self.product_template_ids categories (code starts with 'DI' or 'D', name contains 'DIPLOMADO' case insensitive)
        - self.product_template_id and self.product_template_ids names (contain 'DIPLOMADO' case insensitive)
        - self.code (starts with 'DI' case insensitive)
        """
        self.ensure_one()

        # Check self.code (starts with 'DI' case insensitive)
        if self.code and self.code.upper().startswith('DI'):
            return True

        # Check self.course_type_id
        if self.course_type_id:
            c_type = self.course_type_id
            code_upper = (c_type.code or '').upper()
            name_upper = (c_type.name or '').upper()
            if code_upper.startswith('DI') or code_upper.startswith('D') or 'DIPLOMADO' in name_upper:
                return True

        # Collect products to inspect: product_template_id + product_template_ids
        products = self.env['product.template']
        if 'product_template_id' in self._fields and self.product_template_id:
            products |= self.product_template_id
        if 'product_template_ids' in self._fields and self.product_template_ids:
            products |= self.product_template_ids

        for product in products:
            # Check name (contains 'DIPLOMADO' case insensitive)
            p_name_upper = (product.name or '').upper()
            if 'DIPLOMADO' in p_name_upper:
                return True

            # Check category (code starts with 'DI' or 'D', name contains 'DIPLOMADO' case insensitive)
            if product.categ_id:
                cat = product.categ_id
                cat_code_upper = (getattr(cat, 'code', '') or '').upper()
                cat_name_upper = (cat.name or '').upper()
                if cat_code_upper.startswith('DI') or cat_code_upper.startswith('D') or 'DIPLOMADO' in cat_name_upper:
                    return True

        return False
