# -*- coding: utf-8 -*-
from odoo import api, models


class IrgDiplomadoWizard(models.TransientModel):
    _inherit = 'irg.diplomado.wizard'

    @api.onchange('course_id')
    def _onchange_course_id(self):
        result = super()._onchange_course_id()
        if self.course_id:
            self.duration_hours = self.course_id.irg_diplomado_duration_hours
            self.duration_ects = self.course_id.irg_diplomado_duration_ects
        return result
