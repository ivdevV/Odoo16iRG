# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_title = fields.Boolean(
        string="Es título de carrera",
    )

    view_titulacion = fields.Boolean(string="ver Titulacion", default=False)
    view_practices = fields.Boolean(string="ver Practicas", default=False)
    view_other = fields.Boolean(string="ver Otros servicios", default=False)

