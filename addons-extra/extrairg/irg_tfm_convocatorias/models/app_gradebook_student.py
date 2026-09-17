from odoo import models


_TFM_PROTECTED_GRADEBOOK_FIELDS = frozenset({'admission_id'})


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def write(self, values):
        # ``gradebook_subject_ids`` commands are dispatched by the ORM to the
        # line model, whose own guard rejects reassignment and deletion.
        if _TFM_PROTECTED_GRADEBOOK_FIELDS.intersection(values):
            self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'write')
        return super().write(values)

    def unlink(self):
        # The line rows cascade at database level, so the whole subtree is
        # checked here instead of relying on a nested ORM unlink.
        self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'unlink')
        return super().unlink()
