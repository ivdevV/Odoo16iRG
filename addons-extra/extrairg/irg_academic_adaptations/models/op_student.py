from odoo import fields, models

class OpStudent(models.Model):
    _inherit = 'op.student'
    #exam_attendees_ids = fields.One2many("op.exam.attendees", "student_id",
    #                                     string="Exam attendees")
    #exam_attendees_count = fields.Integer(
    #    compute='_compute_exam_attendees_count', default=0)
    gradebook_ids = fields.One2many("app.gradebook.student", "student_id",
                                         string="Libretas")




    
    #@api.multi
    #def _compute_exam_attendees_count(self):
    #    """
    #    Calcula el numero de calificaciones que posee el estudiante
    #    """
    #    for student in self:
    #        student.exam_attendees_count = len(student.exam_attendees_ids)

    def action_open_exam_attendees(self):
        """Display the linked exam attendees and adapt the view to the
        number of records to display."""
        #self.ensure_one()
        #exam_attendees = self.exam_attendees_ids

        action = self.env.ref('irg_academic_adaptations.act_open_op_exam_attendees_view_new').read()[0]
        action['context'] = {
                'student_id': self.id
        }
        action['domain'] = [('student_id', "=", self.id)]

        value = {
            'name': 'Libretas',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'app.gradebook.student',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_student_id': self.id},
            'domain': [('student_id', "=", self.id)]
        }
        return value


#bretas
