
import logging
# from mailchimp3 import MailChimp
from odoo import api, fields, models, _
from odoo.models import expression
from odoo.exceptions import UserError, ValidationError
import multiprocessing as mp

_logger = logging.getLogger(__name__)


class CrmTeam(models.Model):
    _inherit = 'crm.team'
    x_studio_logo_sede = fields.Binary("Logo Sede")
