# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PracticeRequestFix(models.Model):
    _inherit = 'practice.request'

    # Sobrescribir user_id para agregar default del usuario actual
    user_id = fields.Many2one(
        'res.users',
        string="Usuario Estudiante",
        required=False,  # Quitamos required para evitar problemas
        default=lambda self: self.env.user,
    )

    # Nuevo campo para el estudiante basado en user_id (no stored para mejor reactividad en UI)
    estudiante_id = fields.Many2one(
        'op.student',
        string='Estudiante (Usuario)',
        compute='_compute_estudiante_from_user',
        store=False, # Cambiado a False para evitar problemas de refresco en vista Form
        help="Estudiante asociado al usuario actual."
    )

    @api.depends('user_id')
    def _compute_estudiante_from_user(self):
        """Obtiene el estudiante a partir del usuario"""
        for record in self:
            if record.user_id:
                # Buscar estudiante
                student = self.env['op.student'].sudo().search([
                    ('user_id', '=', record.user_id.id)
                ], limit=1)
                record.estudiante_id = student.id if student else False
            else:
                record.estudiante_id = False

    @api.onchange('user_id')
    def _onchange_user_fill_data(self):
        """Llena automáticamente los datos cuando se selecciona un usuario"""
        # Forzar el calculo del estudiante también en el onchange para la UI
        self._compute_estudiante_from_user()
        
        if self.user_id:
            # Usar el estudiante calculado
            student = self.estudiante_id
            if student:
                self.name = student.name or ''
                self.email = student.email or self.user_id.email or ''
            else:
                self.name = self.user_id.name or ''
                self.email = self.user_id.email or ''
            
            # NOTA: No limpiamos admisión ni curso automáticamente 
            # para evitar que el registro parezca inestable o se borren datos por error.
            # El usuario deberá cambiarlos si el dominio le indica que son inválidos.

