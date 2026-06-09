# -*- coding: utf-8 -*-

from odoo import _, fields, models


class OpStudent(models.Model):
    _inherit = 'op.student'

    academic_request_count = fields.Integer(
        string='Solicitudes Academicas',
        compute='_compute_academic_request_count',
    )

    def _compute_academic_request_count(self):
        Request = self.env['irg.certificate.request'].sudo()
        for student in self:
            domain = [('student_id', '=', student.id)]
            if student.partner_id:
                domain = ['|', ('student_id', '=', student.id), ('partner_id', '=', student.partner_id.id)]
            student.academic_request_count = Request.search_count(domain)

    def action_view_academic_requests(self):
        self.ensure_one()
        action = self.env.ref(
            'irg_gradebook_certificates.action_irg_certificate_request'
        ).sudo().read()[0]
        domain = [('student_id', '=', self.id)]
        if self.partner_id:
            domain = ['|', ('student_id', '=', self.id), ('partner_id', '=', self.partner_id.id)]
        action.update({
            'name': _('Solicitudes Academicas'),
            'domain': domain,
            'context': {
                'default_student_id': self.id,
            },
        })
        return action
