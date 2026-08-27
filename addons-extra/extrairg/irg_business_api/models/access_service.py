# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tools.translate import _

from . import api_serializer as ser


class AccessService:

    def __init__(self, env):
        self.env = env

    def get_student_access(self, payload):
        domain = []
        if payload.get('admission_id'):
            admission = self.env['op.admission'].browse(
                ser.require_positive_id(payload, 'admission_id')
            )
            if not admission.exists():
                raise UserError(_('Unknown admission id.'))
            domain.append(('admission_id', '=', admission.id))
        elif payload.get('partner_id'):
            partner = self.env['res.partner'].browse(
                ser.require_positive_id(payload, 'partner_id')
            )
            if not partner.exists():
                raise UserError(_('Unknown partner id.'))
            domain.append(('partner_id', '=', partner.id))
        else:
            raise UserError(_('admission_id or partner_id is required.'))
        Membership = self.env['slide.channel.partner'].with_context(active_test=False)
        rows = Membership.search(domain, order='id')
        records = []
        for membership in rows:
            row = ser.record_dict(membership, [
                'id', 'channel_id', 'partner_id', 'active',
            ])
            for fname in ('batch_id', 'op_subject_id', 'admission_id', 'date_from', 'date_to', 'completed'):
                if fname in membership._fields:
                    value = membership[fname]
                    row[fname] = value.id if getattr(value, '_name', False) else value
            records.append(row)
        return {'records': records, 'total': len(records)}

    def get_student_academic_360(self, payload):
        admission = self.env['op.admission'].browse(
            ser.require_positive_id(payload, 'admission_id')
        )
        if not admission.exists():
            raise UserError(_('Unknown admission id.'))
        access = self.get_student_access({'admission_id': admission.id})
        openings = self.env['irg.online.subject.opening'].search_count([
            ('admission_id', '=', admission.id),
        ])
        gradebook = {'available': 'app.gradebook.student' in self.env}
        moodle = {'available': 'irg.moodle.grade' in self.env}
        if gradebook['available']:
            books = self.env['app.gradebook.student'].search([
                ('admission_id', '=', admission.id),
            ])
            gradebook['count'] = len(books)
            gradebook['states'] = books.mapped('state')
        if moodle['available'] and admission.partner_id:
            grades = self.env['irg.moodle.grade'].search([
                ('partner_id', '=', admission.partner_id.id),
            ])
            moodle['count'] = len(grades)
            moodle['unmatched'] = len(grades.filtered(lambda row: row.state == 'unmatched_student'))
        return {
            'admission_id': admission.id,
            'course_id': admission.course_id.id if admission.course_id else False,
            'batch_id': admission.batch_id.id if admission.batch_id else False,
            'state': admission.state,
            'access_count': access['total'],
            'opening_count': openings,
            'gradebook': gradebook,
            'moodle': moodle,
        }

    def get_academic_incidents(self, payload):
        records = []
        domain = []
        if payload.get('admission_id'):
            domain.append(('admission_id', '=', ser.require_positive_id(payload, 'admission_id')))
        if 'irg.moodle.grade' in self.env:
            moodle_domain = [('state', '=', 'unmatched_student')]
            if payload.get('admission_id'):
                admission = self.env['op.admission'].browse(payload['admission_id'])
                if admission.partner_id:
                    moodle_domain.append(('partner_id', '=', admission.partner_id.id))
            unmatched = self.env['irg.moodle.grade'].search(moodle_domain, limit=50)
            for row in unmatched:
                records.append({
                    'type': 'moodle_unmatched',
                    'id': row.id,
                    'moodle_user_id': row.moodle_user_id,
                    'state': row.state,
                })
        if 'irg.online.subject.opening' in self.env and payload.get('admission_id'):
            openings = self.env['irg.online.subject.opening'].search(domain)
            for opening in openings.filtered(lambda rec: rec.opening_date and rec.closing_date and rec.opening_date > rec.closing_date):
                records.append({
                    'type': 'opening_inverted_dates',
                    'id': opening.id,
                    'subject_id': opening.subject_id.id,
                })
        return {'records': records, 'total': len(records)}
