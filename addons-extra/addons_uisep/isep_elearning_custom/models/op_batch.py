import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpBatch(models.Model):
    _name = 'op.batch'
    _description = "Asignaturas"


class OpBatch(models.Model):
    _inherit = 'op.batch'

    slide_channel_id = fields.Many2one('slide.channel', string="Asignatura en Elearning")
    subject_ids = fields.Many2many('op.subject', string='Subject(s)')