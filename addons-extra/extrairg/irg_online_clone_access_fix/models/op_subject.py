from odoo import fields, models


class OpSubject(models.Model):
    _inherit = 'op.subject'

    def _irg_partner_online_admissions(self, partner):
        if not partner:
            return self.env['op.admission']
        return self.env['op.admission'].sudo().search([
            ('partner_id', '=', partner.id),
            ('batch_id', '!=', False),
        ])

    def _irg_admission_is_online_for_effective_channel(self, admission):
        if not admission:
            return False
        if hasattr(admission, '_irg_has_online_subject_opening_context'):
            if admission._irg_has_online_subject_opening_context():
                return True
        batch = admission.batch_id
        batch_code = (batch.code or '').upper() if batch else ''
        return bool(batch_code and 'ONL' in batch_code and 'MONL' not in batch_code)

    def _irg_admission_is_active_for_effective_channel(self, admission):
        if not admission:
            return False
        today = fields.Date.today()
        if 'due_date' in admission._fields and admission.due_date and admission.due_date < today:
            return False
        batch = admission.batch_id
        if batch and batch.end_date and batch.end_date < today:
            return False
        return True

    def _irg_should_use_online_slide_channel(self, partner=None, admission=None):
        self.ensure_one()
        if admission:
            return bool(
                self._irg_admission_is_online_for_effective_channel(admission)
                and self._irg_admission_is_active_for_effective_channel(admission)
            )
        admissions = self._irg_partner_online_admissions(partner)
        return any(
            self._irg_admission_is_online_for_effective_channel(candidate)
            and self._irg_admission_is_active_for_effective_channel(candidate)
            for candidate in admissions
        )

    def irg_get_effective_slide_channel(self, partner=None, admission=None):
        self.ensure_one()
        channel = self.slide_channel_id
        if not channel:
            return channel
        online_channel = channel.irg_online_channel_id if 'irg_online_channel_id' in channel._fields else False
        if online_channel and self._irg_should_use_online_slide_channel(partner, admission):
            return online_channel
        return channel
