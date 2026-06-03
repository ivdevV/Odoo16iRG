# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class IrgCertificateWizard(models.TransientModel):
    _inherit = 'irg.certificate.wizard'

    session_id = fields.Many2one(
        'op.session',
        string='Sesión de Clase en Directo',
        domain="[('batch_id', '=', gradebook_batch_id)]",
    )

    gradebook_batch_id = fields.Many2one(
        'op.batch',
        related='gradebook_student_id.batch_id',
        readonly=True,
    )

    def action_generate(self):
        self.ensure_one()
        if self.document_type == 'attendance' and not self.session_id:
            raise models.ValidationError(_("La sesión es obligatoria para certificados de asistencia."))

        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook_student_id.id,
            'document_type': self.document_type,
            'certificate_type': self.certificate_type,
            'shipping_type': self.shipping_type or False,
            'custom_description': self.custom_description or False,
            'custom_options': self.custom_options or False,
            'signer': self.signer,
            'session_id': self.session_id.id if self.document_type == 'attendance' else False,
            'state': 'done',
            'origin': 'backend',
        })
        cert._generate_and_attach_pdf()
        return cert.action_download_pdf()
