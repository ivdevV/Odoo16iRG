# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class FixSurveyUser_input(models.Model):
    _inherit = 'survey.user_input'

    send_to_book = fields.Boolean(string='Enviado a Libreta', default=False)

    def write(self, vals):
        res = super(FixSurveyUser_input, self).write(vals)
        if 'comment' in vals:
            for rec in self:
                if rec.result_id:
                    rec.result_id.comment = vals['comment']
        return res

    def valite_send_result(self):
        for rec in self:
            if (not rec.admission_id or not rec.op_subject_id or not rec.course_id) and hasattr(rec, 'compute_slide_channel_partner'):
                rec.compute_slide_channel_partner()

            if rec.channel_partner_id and rec.partner_id and rec.admission_id and rec.course_id and rec.op_subject_id:
                gradebook_data = rec.channel_partner_id.sudo().search_gradebook_subject(
                    rec.partner_id,
                    rec.admission_id,
                    rec.course_id,
                    rec.op_subject_id
                )
                if gradebook_data.get('gradebook_subject_id'):
                    rec.gradebook_subject_id = gradebook_data['gradebook_subject_id'].id
                    rec.gradebook_student_id = gradebook_data['gradebook_student_id'].id

    def send_result(self):
        rated_by = self.env.user.partner_id.id or False

        for rec in self:
            if rec.admission_id and rec.op_subject_id:
                rec.valite_send_result()
                answer_score_total = rec.answer_score_total or round((rec.scoring_percentage or 0.0) / 10.0, 2)

                result_id = rec.result_id
                if not result_id and rec.gradebook_subject_id:
                    course_id = rec.course_id.name if rec.course_id else 'N/A'
                    application_number = rec.admission_id.application_number if rec.admission_id else 'N/A'
                    description = "%s - %s" % (application_number, course_id)
                    data_survey_type = 'assignment' if rec.survey_type == 'assignment' else 'exam'

                    data = {
                        'name': rec.survey_id.title,
                        'survey_user_input_id': rec.id,
                        'channel_id': rec.channel_id.id,
                        'channel_partner_id': rec.channel_partner_id.id,
                        'scoring_total': answer_score_total,
                        'gradebook_subject_id': rec.gradebook_subject_id.id,
                        'survey_type': data_survey_type,
                        'description': description,
                        'rated_by': rated_by,
                        'comment': rec.comment or ''
                    }
                    result_id = rec.env['app.gradebook.result'].sudo().create(data)
                    rec.send_to_book = True
                elif result_id:
                    result_id.sudo().write({'scoring_total': answer_score_total})

                rec.result_id = result_id
                rec.rated_by = rated_by
