
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #@api.constrains('email')
    #def _check_email_unique(self):
    #    for self in self:
    #        if self.email:
    #            email_count = self.search_count([('email', '=', self.email),('id','!=', self._origin.id)])            
    #            if email_count > 0:
    #                raise UserError("El correo electrónico ya existe.")