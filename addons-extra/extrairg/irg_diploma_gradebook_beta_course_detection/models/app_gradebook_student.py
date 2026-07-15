# -*- coding: utf-8 -*-
import re

from odoo import models


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def _is_diplomado_course(self):
        """Accept an unequivocal Diploma name despite stale classifications."""
        self.ensure_one()
        if super()._is_diplomado_course():
            return True
        if not self.course_id:
            return False

        course_name = self._normalize_text(self.course_id.name)
        return bool(re.search(
            r'(?:^| - )diplomados?(?:\s|$)',
            course_name,
        ))
