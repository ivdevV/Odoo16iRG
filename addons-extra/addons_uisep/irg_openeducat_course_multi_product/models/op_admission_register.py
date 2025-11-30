from odoo import models, fields, api
from odoo.exceptions import UserError

class OpAdmissionRegister(models.Model):
    _inherit = 'op.admission.register'

    product_template_ids = fields.Many2many(
        'product.template',
        'op_admission_register_product_rel',
        'register_id',
        'product_id',
        string="Plantillas de Producto",
        related="course_id.product_template_ids",
        store=True
    )

    @api.constrains('period', 'product_template_ids')
    def _check_validations(self):
        for record in self:
            if record.period:
                if '-' not in record.period or len(record.period) != 7:
                    raise UserError("El periodo debe ser un formato valido, ejemplo: 2025-01")
            
            # Updated validation for multiple products
            # We check if any of the products in this register are already used in another register for the same period
            if record.period and record.product_template_ids:
                for product in record.product_template_ids:
                    domain = [
                        ('period', '=', record.period),
                        ('product_template_ids', 'in', [product.id]),
                        ('id', '!=', record.id)
                    ]
                    if self.env['op.admission.register'].search_count(domain) > 0:
                        raise UserError(f"La combinación entre el periodo y el producto {product.name} ya existe en otro registro.")
