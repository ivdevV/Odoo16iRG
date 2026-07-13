from odoo import api, models


class OpSubjectToBatch(models.Model):
    _inherit = 'op.subject.to.batch'

    _IRG_AUTO_ENROLL_TRIGGER_FIELDS = {'date_from', 'date_to', 'subject_id'}

    def _irg_trigger_auto_enroll_cron(self):
        self.env.ref('isep_elearning_custom.ir_cron_auto_enroll_students')._trigger()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if any(self._IRG_AUTO_ENROLL_TRIGGER_FIELDS.intersection(vals) for vals in vals_list):
            records._irg_trigger_auto_enroll_cron()
        return records

    def write(self, vals):
        result = super().write(vals)
        if self._IRG_AUTO_ENROLL_TRIGGER_FIELDS.intersection(vals):
            self._irg_trigger_auto_enroll_cron()
        return result

    def unlink(self):
        env = self.env
        result = super().unlink()
        env['op.subject.to.batch']._irg_trigger_auto_enroll_cron()
        return result
