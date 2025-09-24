from odoo import fields, models

class OpStudent(models.Model):
    _inherit = 'op.student'
    document_number = fields.Char(string='Document number', size=32)
    document_type_id = fields.Many2one('op.document.type',
                                       string='Document type',
                                       #compute='_compute_document_type',
                                       #store=True
                                       )
