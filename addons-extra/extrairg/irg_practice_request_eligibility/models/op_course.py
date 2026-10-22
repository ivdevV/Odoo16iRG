# -*- coding: utf-8 -*-

from odoo import models


IRG_NC_PRACTICE_COURSE_CODES = frozenset({'NC', 'MNC'})


class OpCourse(models.Model):
    _inherit = 'op.course'

    def irg_is_nc_practice_course(self):
        """Two-year neuropsychology master, sold as NC and mapped as MNC."""
        self.ensure_one()
        return (self.code or '').strip().upper() in IRG_NC_PRACTICE_COURSE_CODES

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
