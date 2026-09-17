from odoo import models


_TFM_PROTECTED_LINE_FIELDS = frozenset({
    'op_subject_id', 'gradebook_student_id',
})


class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    def write(self, values):
        # One2many commands on ``gradebook_result_ids`` reach the result guards
        # through the ORM dispatch, so only the line's own identity is checked
        # here.  The guard locks the hierarchy before looking for a link.
        if _TFM_PROTECTED_LINE_FIELDS.intersection(values):
            self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'write')
        return super().write(values)

    def unlink(self):
        self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'unlink')
        return super().unlink()
