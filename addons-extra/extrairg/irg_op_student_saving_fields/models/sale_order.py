
import logging
# from mailchimp3 import MailChimp
from odoo import api, fields, models, _
from odoo.models import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    x_studio_mes_validacion_matricula = fields.Selection([("Enero","Enero"),("Febrero","Febrero"),("Marzo","Marzo"),("Abril","Abril"),("Mayo","Mayo"),("Junio","Junio"),("Julio","Julio"),("Agosto","Agosto"),("Septiembre","Septiembre"),("Octubre","Octubre"),("Noviembre","Noviembre"),("Diciembre","Diciembre")],string="Mes Validación Matrícula")
    x_studio_ano_validacion_matricula = fields.Selection([("2023","2023"),("2024","2024"),("2025","2025"),("2026","2026"),("2027","2027"),("2028","2028"),("2029","2029"),("2030","2030")],string="Año Validación Matrícula")
    x_studio_importe_neto = fields.Float(string="Importe neto")
