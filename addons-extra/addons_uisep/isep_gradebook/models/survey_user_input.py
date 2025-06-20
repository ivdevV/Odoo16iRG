
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)



class SurveyUserInputWrite(models.TransientModel):
    _name = 'survey.user_input.write'

    survey_id = fields.Many2one('survey.user_input.line', string='survey' )
    answer_score = fields.Float('Score [Puntaje]', related='survey_id.answer_score', readonly=False )
    question_id = fields.Many2one('survey.question',   related='survey_id.question_id',  string='Pregunta' )
    value_file_ids = fields.Many2many(comodel_name='ir.attachment', string='Survey file', readonly=True,  related='survey_id.value_file_ids')

    def save_result(self):        
        return True




class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    result_id = fields.Many2one('app.gradebook.result', string='Resultado en libreta' )

    def open_result(self):
        self.ensure_one()
        ## hace la busqueda de los adjuntos y lo coloca a publico, para tener acceso con cualquier usuario
        ir_attachment = self.env['ir.attachment']
        for file_id in self.value_file_ids:
            ir_attachment_id = ir_attachment.sudo().browse(file_id.id)
            ir_attachment_id.write({'public':True})
        ###        
        data = {
            'survey_id':self.id,
        }
        wizard = self.env['survey.user_input.write'].create(data)

        action = self.env["ir.actions.actions"]._for_xml_id("isep_gradebook.survey_user_input_write_action")        
        action['res_id'] = wizard.id
        return action

    


class SurveyUser_input(models.Model):
    _inherit = 'survey.user_input'

    result_id = fields.Many2one('app.gradebook.result', string='Resultado en libreta' )
    gradebook_student_id = fields.Many2one('app.gradebook.student', string='Libreta de estudiante' )
    gradebook_subject_id = fields.Many2one('app.gradebook.subject', string='Asignatura en libreta' )
    answer_score_total = fields.Float('Puntaje Total', store=True, compute="compute_answer_score_total" )
    rated_by = fields.Many2one('res.partner', string='Calificado por' )
    comment = fields.Text('Comentario')


    @api.depends('user_input_line_ids.answer_score', 'user_input_line_ids.question_id', 'predefined_question_ids.answer_score')
    def _compute_scoring_values(self):
        for user_input in self:
            super(SurveyUser_input, self)._compute_scoring_values()            
            if user_input.survey_type == 'assignment':
                total_possible_score = 10
                score_total = sum(user_input.user_input_line_ids.mapped('answer_score'))
                user_input.scoring_total = score_total
                score_percentage = (score_total / total_possible_score) * 100
                user_input.scoring_percentage = round(score_percentage, 2) if score_percentage > 0 else 0
          

    @api.depends('scoring_percentage')
    def compute_answer_score_total(self):
        answer_score_total=round(self.scoring_percentage/10,2)
        self.answer_score_total = answer_score_total

    @api.model
    def create(self, vals):
        '''The records that are of type exam are created automatically.'''
        res = super(SurveyUser_input, self).create(vals)
        if res.survey_type == 'exam' and not res.test_entry and res.admission_id and res.op_subject_id:
            res.send_result()
        return res
    
    def write(self, values):
        res = super(SurveyUser_input, self).write(values)
        if self.result_id:
            answer_score_total=round(self.scoring_percentage/10,2)
            self.result_id.scoring_total = answer_score_total
        return res


    # EXAM AND ASSIGNMENT
    def send_result(self):
        '''
        Send the results of the exam and assignment type participations to the notebook.
        '''
        rated_by = self.env.user.partner_id.id or False
        result_id = False
        for sp in self.slide_partner_id.user_input_ids:
            if sp.result_id:
                result_id = sp.result_id
                break
        self.result_id = result_id
        if self.admission_id and self.op_subject_id and self.op_subject_id.subject_type == "compulsory":
            answer_score_total = round(self.scoring_percentage/10,2)       
            
            if not self.result_id:
                channel_partner_id = self.channel_partner_id.search_gradebook_subject(self.partner_id,self.admission_id,self.course_id,self.op_subject_id)
                self.gradebook_student_id = channel_partner_id['gradebook_student_id']
                self.gradebook_subject_id = channel_partner_id['gradebook_subject_id']
                course_id = 'N/A'
                application_number = 'N/A'
                if self.course_id:
                    course_id = self.course_id.name
                if self.admission_id:
                    application_number = self.admission_id.application_number
                description = "%s - %s" % (application_number, course_id)
                data = {
                    'name': self.survey_id.title,
                    'survey_user_input_id': self.id,
                    'channel_id': self.channel_id.id,
                    'channel_partner_id': self.channel_partner_id.id,
                    'scoring_total': answer_score_total,
                    'gradebook_subject_id': self.gradebook_subject_id.id,
                    'survey_type': self.survey_type,
                    'description': description,
                    'rated_by': rated_by,
                    'comment': self.comment
                }
                _logger.info(data)
                result_id = self.env['app.gradebook.result'].create(data)
            self.result_id = result_id
            # Identificamos la nota mas alta
            for sp in self.slide_partner_id.user_input_ids:
                if answer_score_total <= sp.answer_score_total:
                    answer_score_total = sp.answer_score_total
            self.result_id.scoring_total = answer_score_total                
            self.rated_by = rated_by

            if not self.gradebook_subject_id:
                self.gradebook_subject_id =  self.result_id.gradebook_subject_id or False
            if not self.gradebook_student_id:
                self.gradebook_student_id =  self.result_id.gradebook_subject_id.gradebook_student_id or False
