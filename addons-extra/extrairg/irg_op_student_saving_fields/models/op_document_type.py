from odoo import models, fields


class OpDocumentType(models.Model):
    _name = "op.document.type"
    _description = "Student document type"

    name = fields.Char('Nombre', size=32, required=True)
    code = fields.Char('Codigo', size=12, required=True)
    required = fields.Boolean('Obligatorio', default=False)
