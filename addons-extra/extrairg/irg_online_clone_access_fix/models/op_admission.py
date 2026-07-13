from datetime import date

import logging

from psycopg2 import IntegrityError

from odoo import models


_logger = logging.getLogger(__name__)
_UNIQUE_INDEX = 'irg_scp_active_partner_channel_batch_uniq'


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def _irg_reconcile_online_clone_channel_partners(self):
        ChannelPartner = self.env['slide.channel.partner'].sudo().with_context(active_test=False)
        for record in self:
            if not record.partner_id or not record.batch_id:
                continue
            if not record.env['op.subject']._irg_admission_is_online_for_effective_channel(record):
                continue

            source_partners = ChannelPartner.search([
                ('partner_id', '=', record.partner_id.id),
                ('admission_id', '=', record.id),
                ('batch_id', '=', record.batch_id.id),
                ('op_subject_id', '!=', False),
                '|',
                ('active', '=', True),
                ('active', '=', False),
            ])
            for source_partner in source_partners:
                subject = source_partner.op_subject_id
                effective_channel = subject.irg_get_effective_slide_channel(record.partner_id, record)
                if not effective_channel or effective_channel == source_partner.channel_id:
                    continue

                clone_partner = ChannelPartner.search([
                    ('partner_id', '=', record.partner_id.id),
                    ('channel_id', '=', effective_channel.id),
                    ('batch_id', '=', record.batch_id.id),
                    '|',
                    ('active', '=', True),
                    ('active', '=', False),
                ], order='active DESC, create_date ASC', limit=1)
                values = source_partner._irg_prepare_online_clone_sync_values()
                values.update({
                    'channel_id': effective_channel.id,
                    'partner_id': record.partner_id.id,
                })
                if clone_partner:
                    clone_partner.with_context(irg_skip_partner_sync=True).write(values)
                else:
                    try:
                        with self.env.cr.savepoint():
                            ChannelPartner.with_context(irg_skip_partner_sync=True).create(values)
                    except IntegrityError as exc:
                        if exc.diag.constraint_name != _UNIQUE_INDEX:
                            raise
                        _logger.info(
                            'Concurrent online clone membership already exists for admission %s',
                            record.id,
                        )

    def _irg_get_opening_effective_slide_channel(self, opening):
        self.ensure_one()
        subject = opening.subject_id
        if subject:
            return subject.irg_get_effective_slide_channel(self.partner_id, self)
        return opening.slide_channel_id

    def _irg_find_online_channel_partner(self, opening):
        self.ensure_one()
        channel = self._irg_get_opening_effective_slide_channel(opening)
        if not channel:
            return self.env['slide.channel.partner']
        return self.env['slide.channel.partner'].sudo().with_context(active_test=False).search([
            ('partner_id', '=', self.partner_id.id),
            ('channel_id', '=', channel.id),
            ('batch_id', '=', self.batch_id.id),
            '|',
            ('active', '=', True),
            ('active', '=', False),
        ], order='active DESC, create_date ASC', limit=1)

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
                channel = record._irg_get_opening_effective_slide_channel(opening)
                if not channel:
                    continue

                channel_partner = record._irg_find_online_channel_partner(opening)
                in_range = opening.opening_date <= today <= opening.closing_date
                can_be_active = in_range and record._irg_subject_precedence_is_satisfied(opening.subject_id)

                if channel_partner:
                    channel_partner.write(record._irg_online_channel_partner_values(opening, can_be_active))
                elif can_be_active:
                    values = record._irg_online_channel_partner_values(opening, True)
                    values.update({
                        'channel_id': channel.id,
                        'partner_id': record.partner_id.id,
                    })
                    record.env['slide.channel.partner'].sudo().create(values)
            record._irg_reconcile_online_clone_channel_partners()

    def auto_enroll_student(self):
        res = super().auto_enroll_student()
        self._irg_reconcile_online_clone_channel_partners()
        return res

    def auto_enroll_student_auto(self):
        res = super().auto_enroll_student_auto()
        self._irg_reconcile_online_clone_channel_partners()
        return res

    def auto_enroll_student_subject(self, subject_id):
        res = super().auto_enroll_student_subject(subject_id)
        self._irg_reconcile_online_clone_channel_partners()
        return res
