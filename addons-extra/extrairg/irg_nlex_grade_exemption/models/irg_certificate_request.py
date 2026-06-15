# -*- coding: utf-8 -*-

from odoo import models


class IrgCertificateRequest(models.Model):
    _inherit = 'irg.certificate.request'

    def _get_certificate_subjects(self):
        subjects = super()._get_certificate_subjects()
        return subjects.filtered(
            lambda s: not s.op_subject_id.irg_is_grade_exempt()
        )
