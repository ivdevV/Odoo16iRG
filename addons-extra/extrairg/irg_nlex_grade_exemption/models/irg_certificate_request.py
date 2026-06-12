# -*- coding: utf-8 -*-

from odoo import models


class IrgCertificateRequest(models.Model):
    _inherit = 'irg.certificate.request'

    def _get_certificate_subjects(self):
        subjects = super()._get_certificate_subjects()
        return subjects.filtered(
            lambda s: not (
                s.op_subject_id.code
                and s.op_subject_id.code.upper().startswith('NLEX')
            )
        )
