# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tools.translate import _

from . import api_serializer as ser


class GradebookService:

    def __init__(self, env):
        self.env = env

    def get_gradebook_summary(self, payload):
        if 'app.gradebook.student' not in self.env:
            return {'available': False, 'results': []}
        domain = []
        if payload.get('admission_id'):
            domain.append(('admission_id', '=', ser.require_positive_id(payload, 'admission_id')))
        elif payload.get('partner_id'):
            domain.append(('partner_id', '=', ser.require_positive_id(payload, 'partner_id')))
        else:
            raise UserError(_('admission_id or partner_id is required.'))
        books = self.env['app.gradebook.student'].search(domain)
        results = []
        for book in books:
            subjects = []
            for subject in book.gradebook_subject_ids:
                source_results = []
                if 'gradebook_result_ids' in subject._fields:
                    for result in subject.gradebook_result_ids:
                        source_results.append({
                            'id': result.id,
                            'survey_type': result.survey_type,
                            'scoring_total': result.scoring_total,
                            'survey_user_input_id': (
                                result.survey_user_input_id.id
                                if result.survey_user_input_id else False
                            ),
                        })
                subjects.append({
                    'id': subject.id,
                    'subject_id': subject.op_subject_id.id if subject.op_subject_id else False,
                    'final_subject_note': (
                        subject.final_subject_note
                        if 'final_subject_note' in subject._fields else False
                    ),
                    'results': source_results,
                })
            results.append({
                'id': book.id,
                'state': book.state,
                'admission_id': book.admission_id.id if book.admission_id else False,
                'subjects': subjects,
            })
        return {'available': True, 'results': results}
