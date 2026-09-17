# -*- coding: utf-8 -*-

from odoo import api, models

IRG_PRACTICE_MODALITY_SYNC_STATES = ('approved', 'progress', 'end')


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_sync_practice_modality_to_enrollment()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ('state', 'practice_center_type_id', 'course_id')):
            self._irg_sync_practice_modality_to_enrollment()
        return res

    def _irg_sync_practice_modality_to_enrollment(self):
        """Copy the latest approved-or-later request type onto each enrollment.

        sudo() is limited to searching this student's requests and writing the
        Many2one on the linked op.student.course. It does not rewrite the request.
        """
        enrollments = self.mapped('course_id')
        Request = self.env['practice.request'].sudo()
        for enrollment in enrollments:
            latest = Request.search([
                ('course_id', '=', enrollment.id),
                ('state', 'in', IRG_PRACTICE_MODALITY_SYNC_STATES),
            ], order='request_date desc, id desc', limit=1)
            if not latest or not latest.practice_center_type_id:
                continue
            if enrollment.irg_practice_center_type_id == latest.practice_center_type_id:
                continue
            enrollment.sudo().write({
                'irg_practice_center_type_id': latest.practice_center_type_id.id,
            })
