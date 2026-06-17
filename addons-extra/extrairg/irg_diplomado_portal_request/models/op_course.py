# -*- coding: utf-8 -*-
from odoo import models


class OpCourse(models.Model):
    _inherit = 'op.course'

    def irg_is_diplomado(self):
        self.ensure_one()
        if self.code and self.code.upper().startswith('DI'):
            return True

        if self.course_type_id:
            code_upper = (self.course_type_id.code or '').upper()
            name_upper = (self.course_type_id.name or '').upper()
            if code_upper.startswith('DI') or code_upper.startswith('D') or 'DIPLOMADO' in name_upper:
                return True

        products = self.env['product.template']
        if 'product_template_id' in self._fields and self.product_template_id:
            products |= self.product_template_id
        if 'product_template_ids' in self._fields and self.product_template_ids:
            products |= self.product_template_ids

        for product in products:
            if 'DIPLOMADO' in (product.name or '').upper():
                return True
            if product.categ_id:
                cat_code = (getattr(product.categ_id, 'code', '') or '').upper()
                cat_name = (product.categ_id.name or '').upper()
                if cat_code.startswith('DI') or cat_code.startswith('D') or 'DIPLOMADO' in cat_name:
                    return True
        return False
