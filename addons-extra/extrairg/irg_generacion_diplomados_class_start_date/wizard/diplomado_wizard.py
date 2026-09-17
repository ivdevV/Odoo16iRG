# -*- coding: utf-8 -*-
from odoo import api, models


class IrgDiplomadoWizard(models.TransientModel):
    _inherit = 'irg.diplomado.wizard'

    def _irg_wizard_batch(self):
        self.ensure_one()
        if not self.student_id or not self.course_id:
            return self.env['op.batch']
        lines = self.student_id.course_detail_ids.filtered(
            lambda line: line.course_id == self.course_id
        )
        finished = lines.filtered(lambda line: line.state == 'finished')
        candidates = finished or lines
        line = candidates.sorted('id', reverse=True)[:1]
        return line.batch_id if line else self.env['op.batch']

    def _irg_apply_class_start_date(self):
        for wizard in self:
            batch = wizard._irg_wizard_batch()
            if not batch:
                continue
            new_date = wizard.env['irg.diplomado.registry']._irg_celebration_start_from_batch(
                batch
            )
            if new_date:
                wizard.start_date = new_date

    @api.onchange('student_id')
    def _onchange_student_id(self):
        result = super()._onchange_student_id()
        self._irg_apply_class_start_date()
        return result

    @api.onchange('course_id')
    def _onchange_course_id(self):
        result = super()._onchange_course_id()
        self._irg_apply_class_start_date()
        return result
