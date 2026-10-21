# -*- coding: utf-8 -*-

import logging

from odoo import fields, models


_logger = logging.getLogger(__name__)

_ACADEMICA_EMAIL = "academica@institutoraimongaja.com"


class AppGradebookStudent(models.Model):
    _inherit = "app.gradebook.student"

    def write(self, vals):
        candidates = self.browse()
        if vals.get("state") == "done":
            candidates = self.filtered(
                lambda gradebook: (
                    gradebook.state != "done"
                    and gradebook.student_id
                    and not gradebook.student_id.sudo().file_closing_date
                )
            )
        result = super().write(vals)
        if candidates:
            self._irg_stamp_expediente_close(candidates)
        return result

    def _irg_stamp_expediente_close(self, candidates):
        template = self.env.ref(
            "irg_gradebook_expediente_close.mail_template_expediente_close",
            raise_if_not_found=False,
        )
        for gradebook in candidates:
            if gradebook.state != "done" or not gradebook.student_id:
                continue
            student = gradebook.student_id.sudo()
            if student.file_closing_date:
                continue
            student.file_closing_date = fields.Date.context_today(gradebook)
            if not template:
                _logger.error(
                    "Expediente close mail template missing for gradebook %s",
                    gradebook.id,
                )
                continue
            try:
                with self.env.cr.savepoint():
                    template.sudo().send_mail(
                        gradebook.id,
                        force_send=True,
                        raise_exception=True,
                        email_values={"email_to": _ACADEMICA_EMAIL},
                    )
            except Exception:
                _logger.exception(
                    "Expediente close notice failed for gradebook %s",
                    gradebook.id,
                )
