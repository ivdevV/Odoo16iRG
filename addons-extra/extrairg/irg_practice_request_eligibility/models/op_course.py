# -*- coding: utf-8 -*-

from odoo import models


class OpCourse(models.Model):
    _inherit = 'op.course'

    def irg_excludes_practice_request(self):
        """True when this course must not open a practice request.

        A course code that starts with DI is always a diplomado. The portal
        tile detector is used when ``course_type_id`` exists; that helper
        reads the field directly and cannot run without it.
        """
        self.ensure_one()
        if (self.code or '').upper().startswith('DI'):
            return True
        if 'course_type_id' not in self._fields:
            return False
        if self.is_diplomado():
            return True
        checker = getattr(self, 'irg_is_diplomado', None)
        return bool(checker and checker())
