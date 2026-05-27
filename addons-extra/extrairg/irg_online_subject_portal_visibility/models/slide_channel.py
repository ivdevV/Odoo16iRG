# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def _irg_is_partner_online_student_for_channel(self, partner):
        self.ensure_one()
        self = self.sudo()
        if not partner:
            _logger.info("[PORTAL_VISIBILITY] No partner provided for channel %s", self.name)
            return False

        today = fields.Date.today()
        admissions = self.env['op.admission'].sudo().search([
            ('partner_id', '=', partner.id)
        ])

        _logger.info("[PORTAL_VISIBILITY] Partner: %s (ID: %s) has %s admissions", partner.name, partner.id, len(admissions))

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

            _logger.info("[PORTAL_VISIBILITY] Admission ID: %s, Batch: %s (Code: %s), is_online (by ONL token): %s, due_date: %s, batch.end_date: %s",
                         admission.id, batch.name, batch.code, is_online, admission.due_date, batch.end_date)

            if is_online:
                # Priorizar due_date de la admisión, usar batch.end_date como fallback
                limit_date = admission.due_date or batch.end_date
                if not limit_date or limit_date >= today:
                    active_batches |= batch
                    _logger.info("[PORTAL_VISIBILITY] -> Added online batch to active_batches: %s", batch.code)
            else:
                if batch.end_date and batch.end_date >= today:
                    active_batches |= batch
                    _logger.info("[PORTAL_VISIBILITY] -> Added traditional batch to active_batches: %s", batch.code)

        if not active_batches:
            _logger.info("[PORTAL_VISIBILITY] -> No active_batches found for partner %s", partner.name)
            return False

        related_courses = self._irg_get_related_courses()
        channel_active_batches = active_batches.filtered(lambda b: b.course_id in related_courses)
        batches_to_check = channel_active_batches or active_batches

        _logger.info("[PORTAL_VISIBILITY] active_batches: %s, related_courses: %s, batches_to_check: %s",
                     active_batches.mapped('code'), related_courses.mapped('code'), batches_to_check.mapped('code'))

        for batch in batches_to_check:
            is_match = self._irg_batch_matches_modality(batch, 'online')
            _logger.info("[PORTAL_VISIBILITY] Batch %s matches modality 'online': %s", batch.code, is_match)
            if is_match:
                return True
        return False

