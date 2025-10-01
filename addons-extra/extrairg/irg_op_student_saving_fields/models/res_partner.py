
import logging
# from mailchimp3 import MailChimp
from odoo import api, fields, models, _
from odoo.models import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    #old_15id = fields.Integer(string='IdOdoo12')
    study_type_id = fields.Many2one('op.study.type', string='Titulacion',
                                    #compute='_compute_study_type', store=True
                                    )
    university_id = fields.Many2one('op.university', string='Universidad',
                                    #compute='_compute_university', store=True
                                    )
    profession_id = fields.Many2one('op.profession', string='Profession',
                                    #compute='_compute_university', store=True
                                    )
