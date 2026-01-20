from odoo import models, fields

class OpCourse(models.Model):
    _inherit = "op.course"

    name_cat = fields.Char(string="Nombre en Català (Diploma)", 
    help="Nombre del curso traducido al Catalán para la impresión de diplomas.")
