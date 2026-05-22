from datetime import date, timedelta

from odoo import api, fields, models


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

    def _irg_subject_precedence_is_satisfied(self, subject):
        self.ensure_one()
        parent_subject = subject.parent_subject_id if hasattr(subject, 'parent_subject_id') else False
        if not parent_subject:
            return True
        # sudo: cron/enrollment must inspect the student's eLearning membership even when run by a limited backend user.
        parent_membership = self.env['slide.channel.partner'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('op_subject_id', '=', parent_subject.id),
            ('admission_id', '=', self.id),
            ('active', '=', True),
        ], limit=1)
        return bool(parent_membership and parent_membership.completed)

    def _irg_find_online_channel_partner(self, opening):
        self.ensure_one()
        # sudo: synchronization owns membership state for the admission and must see active and archived rows.
        return self.env['slide.channel.partner'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('channel_id', '=', opening.slide_channel_id.id),
            ('batch_id', '=', self.batch_id.id),
            '|',
            ('active', '=', True),
            ('active', '=', False),
        ], order='create_date ASC', limit=1)

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

    def cron_auto_enroll_student(self):
        today = date.today()
        online_admissions = self.search([
            ('state', '=', 'done'),
            ('batch_id', '!=', False),
            ('batch_id.code', 'ilike', 'ONL'),
            ('batch_id.code', 'not ilike', 'MONL'),
        ])
        online_admissions._irg_generate_online_subject_openings()
        online_admissions._irg_sync_online_channel_partners()

        other_admissions = self.search([
            ('state', '=', 'done'),
            ('batch_id', '!=', False),
            '|',
            ('batch_id.code', 'not ilike', 'ONL'),
            ('batch_id.code', 'ilike', 'MONL'),
        ])

        for record in other_admissions:
            if hasattr(record, 'modality') and record.modality == 'manual':
                continue

            for subject_batch in record.batch_id.subject_to_batch_ids:
                subject = subject_batch.subject_id
                if not subject.slide_channel_id:
                    continue
                if not subject_batch.date_from or not subject_batch.date_to:
                    continue

                if not record._irg_subject_precedence_is_satisfied(subject):
                    continue

                # sudo: cron reconciles membership rows independently of the current backend user's access rights.
                channel_partner = self.env['slide.channel.partner'].sudo().search([
                    ('partner_id', '=', record.partner_id.id),
                    ('channel_id', '=', subject.slide_channel_id.id),
                    ('batch_id', '=', record.batch_id.id),
                    '|',
                    ('active', '=', True),
                    ('active', '=', False),
                ], order='create_date ASC', limit=1)

                if subject_batch.date_from <= today <= subject_batch.date_to:
                    values = {
                        'active': True,
                        'course_id': record.course_id.id,
                        'register_id': record.register_id.id,
                        'admission_id': record.id,
                        'batch_id': record.batch_id.id,
                        'date_from': subject_batch.date_from,
                        'date_to': subject_batch.date_to,
                        'op_subject_id': subject.id,
                    }
                    if channel_partner:
                        channel_partner.write(values)
                    else:
                        values.update({
                            'channel_id': subject.slide_channel_id.id,
                            'partner_id': record.partner_id.id,
                        })
                        # sudo: cron creates the eLearning membership on behalf of the admitted student.
                        self.env['slide.channel.partner'].sudo().create(values)
                elif today > subject_batch.date_to and channel_partner:
                    channel_partner.write({'active': False})
        return True
