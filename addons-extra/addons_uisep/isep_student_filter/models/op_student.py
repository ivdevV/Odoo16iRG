# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OpStudent(models.Model):
    _inherit = 'op.student'

    sepyc_program = fields.Boolean(string='Programa Sepyc / Sep', default=False)
    university_from = fields.Char(related='partner_id.university', string='Universidad de Procedencia')
    profession_from = fields.Char(related='partner_id.profession', string='Profesión')
    titulacion_from = fields.Char(related='partner_id.titulacion', string='Titulación')
    finalizacionestudios_from = fields.Date(related='partner_id.finalizacionestudios', string='Finalización de Estudios')
    status_student = fields.Selection(
        [('valid', 'Vigente'), ('graduate', 'Graduado'),
         ('low', 'Baja')], default='Vigente', string="Estado de estudiante",
         compute='_compute_determine_status')


    op_admission_ids = fields.One2many(
        'op.admission',
        'student_id',
        string='Admisión',
        compute='_compute_admissions'
    )

    op_course_ids = fields.One2many(
        'op.student.course',
        'student_id',
        string='Curso',
        compute='_compute_admissions'
    )

    file_closing_date = fields.Date('Fecha cierre de expediente')


    def _compute_determine_status(self):
        """
        Determina el estado del estudiante, realiza un recorrido en todas sus admisiones del estudiante
        y verfica el estado de estas mismas, si el estado es cancel se asigna como estado de baja, si la admision 
        posee fecha de cierre expediente academico asignada el estado del estudiante es cambiado a graduado,
        en cualquier otra caso el estado del estudiante es vigente 
        """
        for student in self:
            canceled = []
            graduate = []
            for admission in student.op_admission_ids:
                canceled.append(admission.state == 'cancel')
                graduate.append(True if admission.due_date and fields.Date.today() >= admission.due_date else False)
            if all(canceled):
                student.update({
                    'status_student' : 'low',
                    })
            elif all(graduate):
                student.update({
                    'status_student' : 'graduate',
                })
            else:
                student.update({
                    'status_student' : 'valid',
                })


    
    @api.depends('partner_id')
    def _compute_admissions(self):
        for record in self:
            object_op_admision = self.env['op.admission'].sudo().search([('student_id', '=', record.id)])
            record.op_admission_ids = [(6, 0, object_op_admision.ids)]

            object_op_course = self.env['op.student.course'].sudo().search([('student_id', '=', record.id)])
            record.op_course_ids = [(6, 0, object_op_course.ids)]
