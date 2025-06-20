
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)



class AppGradebookstudent(models.Model):
    _name = 'app.gradebook.student'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Libreta' , store=True, compute="compute_name" )
    student_id = fields.Many2one('op.student', string="Alumno", required=True,  related="admission_id.student_id"  )
    partner_id = fields.Many2one('res.partner', string='Contacto', related="admission_id.partner_id", store=True)
    course_id = fields.Many2one('op.course',  related="admission_id.course_id", string="Curso",   store=True)
    admission_id = fields.Many2one('op.admission', string="Admisión",  store=True, tracking=True  )
    batch_id = fields.Many2one('op.batch', string="Grupo", related="admission_id.batch_id",  store=True)
    
    gradebook_subject_ids = fields.One2many('app.gradebook.subject', 'gradebook_student_id', string="Asignaturas" , tracking=True )

    gradebook_id = fields.Many2one('app.gradebook', string='Calificaciones template' , store=True, compute="compute_gradebook_id" , tracking=True )

    state = fields.Selection(
        string='Estado',
        selection=[('in_progress', 'En proceso'), ('done', 'Finalizado') ], required=True, default="in_progress"
    )


    # @api.constrains('admission_id')
    # def _check_unique_admission_id(self):
    #     for record in self:
    #         existing_record = self.search([('admission_id', '=', record.admission_id.id), ('id', '!=', record.id)])
    #         if existing_record:
    #             raise ValidationError('El campo "Admisión" debe ser único.')
    
    def unlink(self):        
        for rec in self:
            if rec.gradebook_subject_ids:
                for subject in rec.gradebook_subject_ids:
                    if subject.gradebook_result_ids:   
                        raise UserError("Hay evaluaciones registradas, debe eliminar antes todas las evaluaciones.")
           

        return super(AppGradebookstudent, self).unlink()


    def state_to_done(self):
        for rec in self:
            if not rec.gradebook_id:
                UserError('"Calificaciones template" es obligatorio.')
            for subject in rec.gradebook_subject_ids:
                gradebook = subject._get_gradebook_info(subject)
                if gradebook:
                    qty_examn = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'exam'))
                    if gradebook['exam']['qty'] != qty_examn and subject.show_exam:
                        raise UserError('%s: Tiene %s evaluaciones de tipo "Examen" pero necesita %s.'  % (subject.name, qty_examn , gradebook['exam']['qty'] ) ) 
                    
                    qty_assignment = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'assignment'))
                    if gradebook['assignment']['qty'] != qty_assignment  and subject.show_assignment:
                        raise UserError('%s: Tiene %s evaluaciones de tipo "Asignación" pero necesita %s.'  % (subject.name, qty_assignment , gradebook['exam']['qty'] ) ) 
                    

                    qty_foro = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'interaction'))
                    if qty_foro != 1 and subject.show_interaction :
                        raise UserError('%s: Debe tener 1 evaluacion de tipo "Interaccion".' % subject.name)

                    qty_foro = len(subject.gradebook_result_ids.filtered(lambda x: x.survey_type == 'foro'))
                    if qty_foro != 1 and subject.show_foro :
                        raise UserError('%s: Debe tener 1 evaluacion de tipo "Foro".'  % subject.name)
                    
                   

            rec.state = 'done'

    def state_to_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'
    
    @api.depends('course_id')
    def compute_gradebook_id(self):
        for rec in self:
            gradebook_id = False
            if rec.course_id.gradebook_id:
                gradebook_id=rec.course_id.gradebook_id
            rec.gradebook_id = gradebook_id


    @api.depends('course_id','admission_id')
    def compute_name(self):
        for self in self:
            course_id = 'N/A'
            application_number = 'N/A'
            if self.course_id:
                course_id = self.course_id.name
            if self.admission_id:
                application_number = self.admission_id.application_number
            self.name  = "%s - %s"% (application_number, course_id)
    

    