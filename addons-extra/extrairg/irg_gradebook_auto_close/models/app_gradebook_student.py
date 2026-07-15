# -*- coding: utf-8 -*-

import logging

from odoo import models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class AppGradebookStudent(models.Model):
    _inherit = "app.gradebook.student"

    def _irg_is_ready_to_close(self):
        if not self:
            return False
        self.ensure_one()
        if self.state != "in_progress" or not self.gradebook_subject_ids:
            return False

        return all(
            line.final_subject_note > 0
            and (not line.show_exam or line.point_average_exam > 0)
            and (
                not line.show_assignment
                or line.point_average_assignment > 0
            )
            for line in self.gradebook_subject_ids
        )

    def _irg_try_auto_close(self):
        for gradebook in self:
            if not gradebook._irg_is_ready_to_close():
                continue
            try:
                gradebook.state_to_done()
            except UserError as error:
                _logger.warning(
                    "Automatic close skipped for gradebook %s: %s",
                    gradebook.id,
                    error,
                )
