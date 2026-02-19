from odoo import models
from odoo.exceptions import UserError
from odoo.addons.isep_openeducat_sale.models.sale_order import SaleOrder as OpenEducatSaleOrder


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(OpenEducatSaleOrder, self).action_confirm()
        for product in self.order_line.filtered(
            lambda l: not l.display_type
            and l.product_id
            and l.product_template_id
            and l.product_template_id.is_academic_program
            and l.product_template_id.recurring_invoice
        ):
            if not product.product_template_id.course_type:
                raise UserError(
                    'Producto: %s \n\nRequerido "Modalidad": Especificar la modalidad del producto, contacte son el area de Contabilidad o Sistemas.'
                    % (product.product_template_id.display_name)
                )
        return res
