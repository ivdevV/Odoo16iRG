# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class UpdateSurveyBackgroundWizard(models.TransientModel):
    _name = 'update.survey.background.wizard'
    _description = _('UpdateSurveyBackgroundWizard')

    background_image = fields.Binary(string='Nueva Imagen de Fondo')
    firm_response = fields.Binary(string='Nueva Firma de Responsable')
    survey_ids = fields.Many2many(
        'survey.survey',
        domain="[('survey_type', '=', 'cert')]", 
        string='Certificaciones a actualizar'
        )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        surveys = self.env['survey.survey'].browse(active_ids).filtered(lambda s: s.survey_type == 'cert')
        res['survey_ids'] = [(6, 0, surveys.ids)]
        return res


    def action_apply_background(self):
        for survey in self.survey_ids:
            if self.background_image:
                survey.backgroundimage = self.background_image
            if self.firm_response:
                survey.firm_response = self.firm_response
