# -*- coding: utf-8 -*-
from odoo import fields, models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def _irg_is_partner_online_student_for_channel(self, partner):
        self.ensure_one()
        self = self.sudo()
        if not partner:
            return False

        today = fields.Date.today()
        admissions = self.env['op.admission'].sudo().search([
            ('partner_id', '=', partner.id)
        ])

        active_batches = self.env['op.batch'].sudo()
        for admission in admissions:
            batch = admission.batch_id
            if not batch:
                continue

            # Check if it is an online admission
            is_online = False
            if hasattr(admission, 'irg_has_online_subject_opening_context') and admission.irg_has_online_subject_opening_context():
                is_online = True
            else:
                batch_code = batch.code or ''
                if 'ONL' in batch_code and 'MONL' not in batch_code:
                    is_online = True

            if is_online:
                if not admission.due_date or admission.due_date >= today:
                    active_batches |= batch
            else:
                if batch.end_date and batch.end_date >= today:
                    active_batches |= batch

        if not active_batches:
            return False

        related_courses = self._irg_get_related_courses()
        channel_active_batches = active_batches.filtered(lambda b: b.course_id in related_courses)
        batches_to_check = channel_active_batches or active_batches

        for batch in batches_to_check:
            if self._irg_batch_matches_modality(batch, 'online'):
                return True
        return False
