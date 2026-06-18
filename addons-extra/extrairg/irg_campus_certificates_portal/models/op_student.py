# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class OpStudent(models.Model):
    _inherit = 'op.student'

    certificate_request_ids = fields.One2many(
        'irg.certificate.request',
        'student_id',
        string='Solicitudes de Certificados',
    )
    certificate_request_count = fields.Integer(
        string='Cantidad de Certificados',
        compute='_compute_certificate_request_count',
    )

    def _compute_certificate_request_count(self):
        for student in self:
            student.certificate_request_count = len(student.certificate_request_ids)

    def action_view_certificate_requests(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('irg_gradebook_certificates.action_irg_certificate_request')
        action.update({
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        })
        return action
