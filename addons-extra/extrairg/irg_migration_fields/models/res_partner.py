
import logging
# from mailchimp3 import MailChimp
from odoo import api, fields, models, _
from odoo.models import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    #old_15id = fields.Integer(string='IdOdoo12')
    x_studio_titulacion = fields.Char("Titulación")
    x_studio_universidad = fields.Char("Universidad")
    x_studio_date_field_Tme4Y = fields.Date("New Fecha")
    x_studio_ano_de_graduacion = fields.Char("Año de graduación")

