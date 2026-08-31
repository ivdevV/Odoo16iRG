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

    def _admission(self, payload):
        admission = self.env['op.admission'].browse(
            ser.require_positive_id(payload, 'admission_id')
        )
        if not admission.exists():
            raise UserError(_('Unknown admission id.'))
        return admission

    def describe_subject_openings(self, payload):
        admission = self._admission(payload)
        existing = (
            admission.irg_online_subject_opening_ids
            if 'irg_online_subject_opening_ids' in admission._fields
            else self.env['irg.online.subject.opening']
        )
        eligible = False
        if hasattr(admission, '_irg_has_online_subject_opening_context'):
            eligible = bool(admission._irg_has_online_subject_opening_context())
        return {
            'admission_id': admission.id,
            'state': admission.state,
            'eligible': eligible,
            'opening_count': len(existing),
            'opening_ids': existing.ids,
        }

    def preview_apply_subject_opening(self, payload):
        plan = self.describe_subject_openings(payload)
        return plan, dict(plan), {'model': 'op.admission', 'id': plan['admission_id']}

    def apply_subject_opening(self, proposed, before):
        admission = self._admission({'admission_id': proposed['admission_id']})
        if admission.state != before.get('state'):
            raise UserError(_('Admission changed after preview.'))
        if not hasattr(admission, '_irg_generate_online_subject_openings'):
            raise UserError(_('Subject openings are not available.'))
        admission._irg_generate_online_subject_openings()
        openings = admission.irg_online_subject_opening_ids
        return {
            'admission_id': admission.id,
            'opening_count': len(openings),
            'opening_ids': openings.ids,
        }

    def describe_access_reconciliation(self, payload):
        admission = self._admission(payload)
        current = self.get_student_access({'admission_id': admission.id})
        return {
            'admission_id': admission.id,
            'state': admission.state,
            'membership_count': current['total'],
            'active_count': len([row for row in current['records'] if row.get('active')]),
        }

    def preview_apply_access_reconciliation(self, payload):
        plan = self.describe_access_reconciliation(payload)
        return plan, dict(plan), {'model': 'op.admission', 'id': plan['admission_id']}

    def apply_access_reconciliation(self, proposed, before):
        admission = self._admission({'admission_id': proposed['admission_id']})
        if not hasattr(admission, '_irg_sync_online_channel_partners'):
            raise UserError(_('Access reconciliation is not available.'))
        snapshot_before = {}
        if hasattr(admission, '_irg_auto_enroll_membership_snapshot'):
            snapshot_before = admission._irg_auto_enroll_membership_snapshot(admission)
        admission._irg_sync_online_channel_partners()
        if hasattr(admission, '_irg_auto_enroll_membership_snapshot'):
            snapshot_after = admission._irg_auto_enroll_membership_snapshot(admission)
            _activated, archived = admission._irg_auto_enroll_transition_counts(
                snapshot_before, snapshot_after,
            )
            initial_active = sum(1 for active in snapshot_before.values() if active)
            ratio = admission._irg_mass_archive_ratio(initial_active, archived)
            if ratio > 0.30:
                raise UserError(_('Access sync would archive more than 30% of memberships.'))
        access = self.get_student_access({'admission_id': admission.id})
        return {
            'admission_id': admission.id,
            'membership_count': access['total'],
        }

    def describe_enrollment(self, payload):
        admission = self._admission(payload)
        already = admission.state == 'done'
        return {
            'admission_id': admission.id,
            'state': admission.state,
            'student_id': admission.student_id.id if admission.student_id else False,
            'already_enrolled': already,
            'will_call': 'enroll_student' if admission.state == 'confirm' else False,
        }

    def preview_apply_enrollment(self, payload):
        plan = self.describe_enrollment(payload)
        return plan, dict(plan), {'model': 'op.admission', 'id': plan['admission_id']}

    def apply_enrollment(self, proposed, before):
        admission = self._admission({'admission_id': proposed['admission_id']})
        if admission.state != before.get('state'):
            raise UserError(_('Admission changed after preview.'))
        if admission.state == 'done':
            raise UserError(_('Admission is already enrolled.'))
        if admission.state != 'confirm':
            raise UserError(_('Enrollment is only allowed from confirm state via enroll_student.'))
        admission.enroll_student()
        return {
            'admission_id': admission.id,
            'state': admission.state,
            'student_id': admission.student_id.id if admission.student_id else False,
        }

    def describe_withdrawal(self, payload):
        admission = self._admission(payload)
        unpaid = 0
        Move = self.env['account.move']
        order = admission.order_id if 'order_id' in admission._fields else False
        if order and 'order_subscription_id' in Move._fields:
            unpaid = Move.sudo().search_count([
                ('order_subscription_id', '=', order.id),
                ('state', '=', 'posted'),
                ('payment_state', '=', 'not_paid'),
            ])
        return {
            'admission_id': admission.id,
            'state': admission.state,
            'would_call_action_down': False,
            'unpaid_invoices': unpaid,
            'refused': True,
            'reason': 'action_down is not exposed; it can cancel unpaid invoices.',
        }

    def preview_apply_withdrawal(self, payload):
        plan = self.describe_withdrawal(payload)
        return plan, dict(plan), {'model': 'op.admission', 'id': plan['admission_id']}

    def apply_withdrawal(self, proposed, before):
        raise UserError(_(
            'Withdrawal via action_down() is not available on the business API. '
            'Use the official admission UI.'
        ))

    def get_access_exceptions(self, payload):
        admission = self._admission(payload)
        incidents = self.get_academic_incidents({'admission_id': admission.id})
        access = self.get_student_access({'admission_id': admission.id})
        archived = [row for row in access['records'] if not row.get('active')]
        return {
            'admission_id': admission.id,
            'incidents': incidents['records'],
            'archived_memberships': len(archived),
            'total': incidents['total'] + len(archived),
        }

