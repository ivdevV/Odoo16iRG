# -*- coding: utf-8 -*-
import re

from odoo import models


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def _is_presential_module_subject(self, gradebook_subject):
        """Match the complete phrase in either available subject label.

        ``app.gradebook.subject.name`` is stored and can retain the label
        shown to users even when the current ``op.subject`` name differs.
        Both values therefore need to be evaluated independently.
        """
        candidate_names = (
            gradebook_subject.op_subject_id.name,
            gradebook_subject.name,
        )
        pattern = r'(?<!\w)modulo presencial(?!\w)'
        return any(
            re.search(pattern, self._normalize_text(name))
            for name in candidate_names
            if name
        )
