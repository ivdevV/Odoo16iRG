from odoo import models


_TFM_PROTECTED_ADMISSION_FIELDS = frozenset({
    'student_id', 'course_id', 'batch_id',
})


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def write(self, values):
        # The gradebook derives its student, course and batch from the admission,
        # so this triple is part of the identity a linked TFM result depends on.
        if _TFM_PROTECTED_ADMISSION_FIELDS.intersection(values):
            self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'write')
        return super().write(values)

    def unlink(self):
        self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'unlink')
        return super().unlink()
