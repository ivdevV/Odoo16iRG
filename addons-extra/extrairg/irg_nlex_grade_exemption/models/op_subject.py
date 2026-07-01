# -*- coding: utf-8 -*-

from odoo import models


class OpSubject(models.Model):
    _inherit = 'op.subject'

    def irg_is_grade_exempt(self):
        """Single source of truth for grade-exemption matching.

        A subject is exempt (excluded from gradebook closing validation,
        averages, DEC export, certificates and printed reports) when its
        code contains the marker ``EX`` (case-insensitive). This covers the
        legacy ``NLEX*`` codes as well as any other ``*EX*`` code.

        Public (no leading underscore) so QWeb templates can call it.
        """
        if not self:
            return False
        self.ensure_one()
        return bool(self.code and 'EX' in self.code.upper())
