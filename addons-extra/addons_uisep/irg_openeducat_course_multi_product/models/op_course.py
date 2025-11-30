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

    @api.model
    def _sync_product_fields(self):
        """
        One-time sync method to populate product_template_ids from product_template_id
        This should be called after module upgrade
        """
        courses = self.search([('product_template_id', '!=', False), ('product_template_ids', '=', False)])
        for course in courses:
            course.product_template_ids = [(6, 0, [course.product_template_id.id])]
        return True

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to sync product_template_id to product_template_ids"""
        records = super(OpCourse, self).create(vals_list)
        for record in records:
            if record.product_template_id and not record.product_template_ids:
                record.product_template_ids = [(6, 0, [record.product_template_id.id])]
            
            # Sync ids -> id when creating with product_template_ids but no product_template_id
            if not record.product_template_id and record.product_template_ids:
                 self.env.cr.execute(
                    "UPDATE op_course SET product_template_id = %s WHERE id = %s",
                    (record.product_template_ids[0].id, record.id)
                 )
                 record.invalidate_recordset(['product_template_id'])
        return records

    def write(self, vals):
        """Override write to sync between product_template_id and product_template_ids"""
        # If product_template_id is being updated, we'll sync it to product_template_ids after the write
        sync_to_many2many = 'product_template_id' in vals and 'product_template_ids' not in vals
        # If product_template_ids is being updated, we'll sync it to product_template_id after the write  
        sync_to_many2one = 'product_template_ids' in vals and 'product_template_id' not in vals
        
        res = super(OpCourse, self).write(vals)
        
        if sync_to_many2many:
            for course in self:
                if course.product_template_id:
                    course.product_template_ids = [(6, 0, [course.product_template_id.id])]
                else:
                    course.product_template_ids = [(5, 0, 0)]
        
        if sync_to_many2one:
            for course in self:
                if course.product_template_ids:
                    # Use direct SQL to avoid recursion
                    self.env.cr.execute(
                        "UPDATE op_course SET product_template_id = %s WHERE id = %s",
                        (course.product_template_ids[0].id, course.id)
                    )
                else:
                    self.env.cr.execute(
                        "UPDATE op_course SET product_template_id = NULL WHERE id = %s",
                        (course.id,)
                    )
            # Invalidate cache after direct SQL update
            self.invalidate_recordset(['product_template_id'])
        
        return res
