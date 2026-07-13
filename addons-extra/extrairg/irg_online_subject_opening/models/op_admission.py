from datetime import date, timedelta

import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    irg_online_subject_opening_ids = fields.One2many(
        'irg.online.subject.opening',
        'admission_id',
        string='Aperturas online por asignatura',
        readonly=True,
    )
    irg_is_online_subject_opening = fields.Boolean(
        string='Calendario online individual',
        compute='_compute_irg_is_online_subject_opening',
        store=True,
    )

    @api.depends('batch_id.code', 'batch_id.subject_to_batch_ids.date_from', 'batch_id.subject_to_batch_ids.date_to')
    def _compute_irg_is_online_subject_opening(self):
        for record in self:
            record.irg_is_online_subject_opening = record._irg_is_online_subject_opening_batch()

    def _irg_is_online_subject_opening_batch(self):
        self.ensure_one()
        batch_code = (self.batch_id.code or '').upper()
        if not (batch_code and 'ONL' in batch_code and 'MONL' not in batch_code):
            return False
        # Si el lote ya tiene fechas en sus asignaturas, usar lógica de lote (no ventanas individuales)
        return not self.batch_id.subject_to_batch_ids.filtered(
            lambda s: s.date_from and s.date_to
        )

    def _irg_has_online_subject_opening_context(self):
        self.ensure_one()
        return bool(
            self._irg_is_online_subject_opening_batch()
            and self.admission_date
            and self.course_id
            and self.batch_id
        )

    def _irg_get_ordered_online_subjects(self):
        self.ensure_one()
        subjects = self.batch_id.subject_to_batch_ids.mapped('subject_id')
        if not subjects:
            subjects = self.course_id.subject_ids
        return subjects.sorted(lambda subject: ((subject.code or '').upper(), subject.name or '', subject.id))

    def _irg_prepare_subject_opening_values(self, subject, sequence):
        self.ensure_one()
        opening_date = self.admission_date + timedelta(days=30 * sequence)
        return {
            'admission_id': self.id,
            'course_id': self.course_id.id,
            'batch_id': self.batch_id.id,
            'subject_id': subject.id,
            'sequence': sequence + 1,
            'opening_date': opening_date,
            'closing_date': opening_date + timedelta(days=29),
        }

    def _irg_generate_online_subject_openings(self):
        Opening = self.env['irg.online.subject.opening']
        for record in self:
            existing_openings = record.irg_online_subject_opening_ids
            if not record._irg_has_online_subject_opening_context():
                existing_openings.unlink()
                continue

            values_by_subject = {
                subject.id: record._irg_prepare_subject_opening_values(subject, sequence)
                for sequence, subject in enumerate(record._irg_get_ordered_online_subjects())
            }

            existing_by_subject = {opening.subject_id.id: opening for opening in existing_openings}
            for subject_id, values in values_by_subject.items():
                opening = existing_by_subject.get(subject_id)
                if opening:
                    opening.write(values)
                else:
                    Opening.create(values)

            obsolete_openings = existing_openings.filtered(lambda opening: opening.subject_id.id not in values_by_subject)
            obsolete_openings.unlink()

    def _irg_get_online_openings_for_date(self, target_date=None):
        self.ensure_one()
        target_date = target_date or fields.Date.context_today(self)
        if not self.irg_online_subject_opening_ids and self._irg_has_online_subject_opening_context():
            self._irg_generate_online_subject_openings()
        return self.irg_online_subject_opening_ids.filtered(
            lambda opening: opening.opening_date <= target_date <= opening.closing_date
        )

    def _irg_get_visible_online_subjects_for_date(self, target_date=None):
        self.ensure_one()
        return self._irg_get_online_openings_for_date(target_date).mapped('subject_id')

    def irg_has_online_subject_opening_context(self):
        self.ensure_one()
        return self._irg_has_online_subject_opening_context()

    def irg_get_visible_online_subjects_for_date(self, target_date=None):
        self.ensure_one()
        return self._irg_get_visible_online_subjects_for_date(target_date)

    def _irg_can_sync_online_openings(self):
        self.ensure_one()
        return bool(
            self.state == 'done'
            and self.partner_id
            and self.register_id
            and self._irg_has_online_subject_opening_context()
        )

    def _irg_find_online_channel_partner(self, opening):
        self.ensure_one()
        # sudo: synchronization owns membership state for the admission and must see active and archived rows.
        return self.env['slide.channel.partner'].sudo().with_context(active_test=False).search([
            ('partner_id', '=', self.partner_id.id),
            ('channel_id', '=', opening.slide_channel_id.id),
            ('batch_id', '=', self.batch_id.id),
            '|',
            ('active', '=', True),
            ('active', '=', False),
        ], order='active DESC, create_date ASC', limit=1)

    def _irg_online_channel_partner_values(self, opening, active):
        self.ensure_one()
        return {
            'active': active,
            'course_id': self.course_id.id,
            'register_id': self.register_id.id,
            'admission_id': self.id,
            'batch_id': self.batch_id.id,
            'date_from': opening.opening_date,
            'date_to': opening.closing_date,
            'op_subject_id': opening.subject_id.id,
        }

    def _irg_sync_online_channel_partners(self, subject_domain=None):
        today = date.today()
        for record in self:
            if not record._irg_can_sync_online_openings():
                continue

            record._irg_generate_online_subject_openings()
            openings = record.irg_online_subject_opening_ids
            if subject_domain:
                openings = openings.filtered(subject_domain)

            for opening in openings:
                if not opening.slide_channel_id:
                    continue

                channel_partner = record._irg_find_online_channel_partner(opening)
                in_range = opening.opening_date <= today <= opening.closing_date
                can_be_active = in_range and record._irg_subject_precedence_is_satisfied(opening.subject_id)

                if channel_partner:
                    channel_partner.write(record._irg_online_channel_partner_values(opening, can_be_active))
                elif can_be_active:
                    values = record._irg_online_channel_partner_values(opening, True)
                    values.update({
                        'channel_id': opening.slide_channel_id.id,
                        'partner_id': record.partner_id.id,
                    })
                    # sudo: cron/enrollment creates the membership on behalf of the admitted student.
                    record.env['slide.channel.partner'].sudo().create(values)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_generate_online_subject_openings()
        return records

    def write(self, vals):
        res = super().write(vals)
        trigger_fields = {'admission_date', 'batch_id', 'course_id', 'state'}
        if trigger_fields.intersection(vals):
            self._irg_generate_online_subject_openings()
        return res

    def enroll_student(self):
        res = super().enroll_student()
        self._irg_generate_online_subject_openings()
        self._irg_sync_online_channel_partners()
        return res

    def auto_enroll_student(self):
        online_records = self.filtered(lambda record: record._irg_has_online_subject_opening_context())
        other_records = self - online_records
        if other_records:
            super(OpAdmission, other_records).auto_enroll_student()
        online_records._irg_sync_online_channel_partners()
        return True

    def auto_enroll_student_auto(self):
        online_records = self.filtered(lambda record: record._irg_has_online_subject_opening_context())
        other_records = self - online_records
        if other_records:
            super(OpAdmission, other_records).auto_enroll_student_auto()
        online_records._irg_sync_online_channel_partners()
        return True

    def auto_enroll_student_subject(self, subject_id):
        online_records = self.filtered(lambda record: record._irg_has_online_subject_opening_context())
        other_records = self - online_records
        if other_records:
            super(OpAdmission, other_records).auto_enroll_student_subject(subject_id)
        online_records._irg_sync_online_channel_partners(
            subject_domain=lambda opening: opening.subject_id.parent_subject_id.id == subject_id
        )
        return True

    def _irg_auto_enroll_membership_snapshot(self, admissions):
        pairs = {(record.partner_id.id, record.batch_id.id) for record in admissions
                 if record.partner_id and record.batch_id}
        if not pairs:
            return {}
        domain = expression.OR([
            [('partner_id', '=', partner_id), ('batch_id', '=', batch_id)]
            for partner_id, batch_id in pairs
        ])
        memberships = self.env['slide.channel.partner'].sudo().with_context(
            active_test=False,
        ).search(domain)
        return {membership.id: membership.active for membership in memberships}

    def _irg_auto_enroll_transition_counts(self, before, after):
        activated = sum(
            1 for membership_id, is_active in after.items()
            if is_active and not before.get(membership_id, False)
        )
        archived = sum(
            1 for membership_id, was_active in before.items()
            if was_active and membership_id in after and not after[membership_id]
        )
        return activated, archived

    def _irg_mass_archive_ratio(self, initial_active_count, archived_count):
        return archived_count / initial_active_count if initial_active_count else 0.0

    def _irg_auto_enroll_domain(self):
        """Keep the effective cron autonomous from optional robustness extensions."""
        return [('state', '=', 'done'), ('batch_id', '!=', False)]

    def cron_auto_enroll_student(self):
        admissions = self.search(self._irg_auto_enroll_domain())
        _logger.info('Auto-enroll start: admissions=%s', len(admissions))
        with self.env.cr.savepoint():
            before = self._irg_auto_enroll_membership_snapshot(admissions)
            processed = errors = 0
            for record in admissions:
                try:
                    with self.env.cr.savepoint():
                        record.auto_enroll_student()
                    processed += 1
                except Exception:
                    errors += 1
                    _logger.exception('Auto-enroll failed for admission %s', record.id)
            after = self._irg_auto_enroll_membership_snapshot(admissions)
            activated, archived = self._irg_auto_enroll_transition_counts(before, after)
            initial_active = sum(1 for active in before.values() if active)
            ratio = self._irg_mass_archive_ratio(initial_active, archived)
            _logger.info(
                'Auto-enroll end: processed=%s activated=%s archived=%s errors=%s',
                processed, activated, archived, errors,
            )
            if ratio > 0.30:
                _logger.warning(
                    'Auto-enroll mass archive blocked: activated=%s archived=%s '
                    'initial_active=%s ratio=%.2f%%',
                    activated, archived, initial_active, ratio * 100,
                )
                raise ValidationError('Auto-enroll mass archive guard exceeded 30%')
        return True
