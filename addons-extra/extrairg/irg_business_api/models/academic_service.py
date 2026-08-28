# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tools.translate import _

from . import api_serializer as ser


class AcademicService:

    def __init__(self, env):
        self.env = env

    def list_academic_periods(self, payload):
        years = self.env['op.academic.year'].search([], order='id desc')
        page, meta = ser.paginate(years, payload)
        year_fields = ['id', 'name', 'start_date', 'end_date']
        data = {
            'years': [ser.record_dict(year, year_fields) for year in page],
            'terms': [],
            'campuses': [],
            'pagination': meta,
        }
        if page and 'op.academic.term' in self.env:
            terms = self.env['op.academic.term'].search([
                ('academic_year_id', 'in', page.ids),
            ])
            term_fields = ['id', 'name', 'academic_year_id', 'term_start_date', 'term_end_date']
            data['terms'] = [ser.record_dict(term, term_fields) for term in terms]
        if 'op.campus' in self.env:
            campuses = self.env['op.campus'].search([], limit=meta['limit'])
            data['campuses'] = [ser.record_dict(campus, ['id', 'name', 'code']) for campus in campuses]
        return data

    def list_courses(self, payload):
        domain = []
        if payload.get('name'):
            domain.append(('name', 'ilike', payload['name']))
        if payload.get('code'):
            domain.append(('code', 'ilike', payload['code']))
        courses = self.env['op.course'].search(domain, order='id')
        page, meta = ser.paginate(courses, payload)
        records = []
        for course in page:
            row = ser.record_dict(course, ['id', 'name', 'code'])
            if 'irg_modality_ids' in course._fields:
                row['modalities'] = [
                    ser.record_dict(mod, ['id', 'name'])
                    for mod in course.irg_modality_ids
                ]
            records.append(row)
        return {'records': records, 'pagination': meta}

    def get_course_overview(self, payload):
        course = self._browse_or_raise('op.course', ser.require_positive_id(payload, 'course_id'))
        data = ser.record_dict(course, ['id', 'name', 'code'])
        data['modalities'] = []
        if 'irg_modality_ids' in course._fields:
            data['modalities'] = [
                ser.record_dict(mod, ['id', 'name']) for mod in course.irg_modality_ids
            ]
        data['convocatorias'] = []
        data['channels'] = []
        if 'irg.course.convocatoria' in self.env:
            convocatorias = self.env['irg.course.convocatoria'].search([
                ('batch_ids.course_id', '=', course.id),
            ])
            for conv in convocatorias:
                row = ser.record_dict(conv, ['id', 'name', 'modality', 'year', 'channel_id'])
                row['batch_ids'] = conv.batch_ids.ids
                data['convocatorias'].append(row)
                if conv.channel_id:
                    data['channels'].append(ser.record_dict(
                        conv.channel_id, ['id', 'name', 'is_published']
                    ))
        return data

    def get_course_batches(self, payload):
        course = self._browse_or_raise('op.course', ser.require_positive_id(payload, 'course_id'))
        batches = self.env['op.batch'].search([('course_id', '=', course.id)], order='id')
        page, meta = ser.paginate(batches, payload)
        records = []
        for batch in page:
            row = ser.record_dict(batch, ['id', 'name', 'code', 'start_date', 'end_date', 'course_id'])
            subjects = []
            if 'subject_to_batch_ids' in batch._fields:
                for line in batch.subject_to_batch_ids:
                    subjects.append({
                        'subject_id': line.subject_id.id,
                        'subject_name': line.subject_id.name,
                        'date_from': line.date_from,
                        'date_to': line.date_to,
                    })
            row['subjects'] = subjects
            records.append(row)
        return {'records': records, 'pagination': meta}

    def list_subjects(self, payload):
        domain = []
        if payload.get('course_id'):
            course = self._browse_or_raise(
                'op.course', ser.require_positive_id(payload, 'course_id')
            )
            domain.append(('id', 'in', course.subject_ids.ids))
        subjects = self.env['op.subject'].search(domain, order='id')
        page, meta = ser.paginate(subjects, payload)
        records = []
        for subject in page:
            row = ser.record_dict(subject, ['id', 'name', 'code', 'subject_type'])
            row['parent_subject_id'] = (
                subject.parent_subject_id.id
                if 'parent_subject_id' in subject._fields and subject.parent_subject_id
                else False
            )
            records.append(row)
        return {'records': records, 'pagination': meta}

    def get_admission_overview(self, payload):
        admission = self._browse_or_raise(
            'op.admission', ser.require_positive_id(payload, 'admission_id')
        )
        data = ser.record_dict(admission, [
            'id', 'name', 'state', 'course_id', 'batch_id',
            'application_number', 'admission_date', 'email',
        ])
        data['partner_id'] = admission.partner_id.id if admission.partner_id else False
        data['partner_name'] = admission.partner_id.name if admission.partner_id else False
        return data

    def get_admission_subject_openings(self, payload):
        admission = self._browse_or_raise(
            'op.admission', ser.require_positive_id(payload, 'admission_id')
        )
        Opening = self.env['irg.online.subject.opening']
        openings = Opening.search([('admission_id', '=', admission.id)], order='sequence, id')
        records = [
            ser.record_dict(opening, [
                'id', 'subject_id', 'subject_code', 'batch_id', 'course_id',
                'opening_date', 'closing_date', 'sequence', 'active',
            ])
            for opening in openings
        ]
        return {'records': records, 'total': len(records)}

    def get_survey_structure(self, payload):
        if 'survey.survey' not in self.env:
            raise UserError(_('Survey model is not installed.'))
        survey = self._browse_or_raise(
            'survey.survey', ser.require_positive_id(payload, 'survey_id')
        )
        data = ser.record_dict(survey, ['id', 'title', 'state', 'scoring_type'])
        questions = []
        Question = self.env['survey.question']
        question_records = Question.search([('survey_id', '=', survey.id)], order='sequence, id')
        for question in question_records:
            qrow = ser.record_dict(question, [
                'id', 'title', 'question_type', 'sequence', 'constr_mandatory',
            ])
            answers = []
            if 'suggested_answer_ids' in question._fields:
                for answer in question.suggested_answer_ids:
                    answers.append(ser.record_dict(answer, [
                        'id', 'value', 'is_correct', 'answer_score',
                    ]))
            qrow['answers'] = answers
            questions.append(qrow)
        data['questions'] = questions
        return data

    def get_batch_schedule(self, payload):
        batch = self._browse_or_raise('op.batch', ser.require_positive_id(payload, 'batch_id'))
        lines = []
        if 'op.subject.to.batch' not in self.env:
            return {'batch_id': batch.id, 'records': []}
        rows = self.env['op.subject.to.batch'].search([('batch_id', '=', batch.id)])
        for row in rows:
            item = ser.record_dict(row, ['id', 'code'])
            item['subject_id'] = row.subject_id.id if row.subject_id else False
            item['date_from'] = row.date_from if 'date_from' in row._fields else False
            item['date_to'] = row.date_to if 'date_to' in row._fields else False
            lines.append(item)
        return {'batch_id': batch.id, 'course_id': batch.course_id.id, 'records': lines}

    def describe_batch_schedule_sync(self, payload):
        batch = self._browse_or_raise('op.batch', ser.require_positive_id(payload, 'batch_id'))
        current = self.get_batch_schedule(payload)
        lines = payload.get('lines') or []
        if not isinstance(lines, list):
            raise UserError(_('lines must be a list.'))
        proposed_lines = []
        for line in lines:
            if not isinstance(line, dict):
                raise UserError(_('Each schedule line must be an object.'))
            subject_id = ser.require_positive_id(line, 'subject_id')
            subject = self._browse_or_raise('op.subject', subject_id)
            if subject not in batch.course_id.subject_ids:
                raise UserError(_('Subject %s does not belong to the batch course.') % subject_id)
            proposed_lines.append({
                'subject_id': subject.id,
                'date_from': line.get('date_from') or False,
                'date_to': line.get('date_to') or False,
            })
        return {
            'batch_id': batch.id,
            'current': current['records'],
            'lines': proposed_lines,
        }

    def preview_apply_batch_schedule_sync(self, payload):
        plan = self.describe_batch_schedule_sync(payload)
        return {'batch_id': plan['batch_id']}, plan, {'model': 'op.batch', 'id': plan['batch_id']}

    def apply_batch_schedule_sync(self, proposed, before):
        batch = self._browse_or_raise('op.batch', proposed['batch_id'])
        Line = self.env['op.subject.to.batch']
        written = []
        for line in proposed.get('lines') or []:
            row = Line.search([
                ('batch_id', '=', batch.id),
                ('subject_id', '=', line['subject_id']),
            ], limit=1)
            vals = {}
            if 'date_from' in Line._fields:
                vals['date_from'] = line.get('date_from') or False
            if 'date_to' in Line._fields:
                vals['date_to'] = line.get('date_to') or False
            if row:
                row.write(vals)
            else:
                vals.update({'batch_id': batch.id, 'subject_id': line['subject_id']})
                row = Line.create(vals)
            written.append(row.id)
        return {'batch_id': batch.id, 'line_ids': written}

    def describe_subject_precedence(self, payload):
        subject = self._browse_or_raise('op.subject', ser.require_positive_id(payload, 'subject_id'))
        admission = self._browse_or_raise(
            'op.admission', ser.require_positive_id(payload, 'admission_id')
        )
        parent = subject.parent_subject_id if 'parent_subject_id' in subject._fields else False
        return {
            'subject_id': subject.id,
            'admission_id': admission.id,
            'parent_subject_id': parent.id if parent else False,
        }

    def get_student_subject_eligibility(self, payload):
        subject = self._browse_or_raise('op.subject', ser.require_positive_id(payload, 'subject_id'))
        admission = self._browse_or_raise(
            'op.admission', ser.require_positive_id(payload, 'admission_id')
        )
        eligible = False
        evidence = 'can_be_taken unavailable'
        user = False
        if admission.student_id and admission.student_id.user_id:
            user = admission.student_id.user_id
        elif admission.partner_id:
            user = self.env['res.users'].search([('partner_id', '=', admission.partner_id.id)], limit=1)
        if user and hasattr(subject, 'can_be_taken'):
            eligible = bool(subject.can_be_taken(user.id, admission=admission))
            evidence = 'op.subject.can_be_taken'
        return {
            'subject_id': subject.id,
            'admission_id': admission.id,
            'can_be_taken': eligible,
            'evidence': evidence,
        }

    def _browse_or_raise(self, model_name, record_id):
        record = self.env[model_name].browse(record_id)
        if not record.exists():
            raise UserError(_('%s id %s was not found.') % (model_name, record_id))
        return record
