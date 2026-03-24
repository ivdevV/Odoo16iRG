# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    certificate_count = fields.Integer(
        string='Certificados',
        compute='_compute_certificate_count',
    )

    def _compute_certificate_count(self):
        Cert = self.env['irg.certificate.request']
        for rec in self:
            rec.certificate_count = Cert.search_count(
                [('gradebook_student_id', '=', rec.id)]
            )

    def action_open_certificate_wizard(self):
        """Open the certificate-generation wizard pre-filled with this gradebook."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generar Certificado de Notas'),
            'res_model': 'irg.certificate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id, 'active_model': 'app.gradebook.student'},
        }

    def action_view_certificates(self):
        """Open the list of certificate requests linked to this gradebook."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Certificados de Notas'),
            'res_model': 'irg.certificate.request',
            'view_mode': 'tree,form',
            'domain': [('gradebook_student_id', '=', self.id)],
            'context': {'default_gradebook_student_id': self.id},
        }
