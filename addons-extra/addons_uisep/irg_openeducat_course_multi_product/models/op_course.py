from odoo import models, fields, api

class OpCourse(models.Model):
    _inherit = 'op.course'

    product_template_ids = fields.Many2many(
        'product.template',
        'op_course_product_rel',
        'course_id',
        'product_id',
        string="Productos",
        help="Productos asociados a este curso."
    )

    # Migration logic or compute to sync old field if needed
    # For now, we just add the new field.
