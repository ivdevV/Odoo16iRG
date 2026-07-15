# -*- coding: utf-8 -*-

from odoo import api, models


_IRG_SKIP_NESTED_WRITE_AUTO_CLOSE = (
    "irg_gradebook_auto_close_skip_nested_write_auto_close"
)


class AppGradebookResult(models.Model):
    _inherit = "app.gradebook.result"

    @api.model_create_multi
    def create(self, vals_list):
        records = self.browse()
        create_model = self.with_context(
            **{_IRG_SKIP_NESTED_WRITE_AUTO_CLOSE: True}
        )
        for values in vals_list:
            created = super(AppGradebookResult, create_model).create(values)
            records |= self.browse(created.ids)

        gradebooks = records.mapped(
            "gradebook_subject_id.gradebook_student_id"
        )
        gradebooks._irg_try_auto_close()
        return records

    def write(self, values):
        previous_gradebooks = self.mapped(
            "gradebook_subject_id.gradebook_student_id"
        )
        result = True
        for record in self:
            result = super(AppGradebookResult, record).write(dict(values))
        if self.env.context.get(_IRG_SKIP_NESTED_WRITE_AUTO_CLOSE):
            return result
        current_gradebooks = self.mapped(
            "gradebook_subject_id.gradebook_student_id"
        )
        (previous_gradebooks | current_gradebooks).exists()._irg_try_auto_close()
        return result

    def unlink(self):
        gradebooks = self.mapped(
            "gradebook_subject_id.gradebook_student_id"
        )
        result = super().unlink()
        gradebooks.exists()._irg_try_auto_close()
        return result
