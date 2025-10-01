
import logging
# from mailchimp3 import MailChimp
from odoo import api, fields, models, _
from odoo.models import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    x_studio_modalidad = fields.Selection([("Online","Online"),("Presencial","Presencial"),("Homeclass","Homeclass")],string="Modalidad")
    x_studio_titulacin = fields.Selection([("Propio","Propia"),("Oficial Universitario","Oficial Universitaria")],string="Titulación")
    x_studio_grupo_acadmico = fields.Many2one("practice.schedule", string="Grupo académico")
