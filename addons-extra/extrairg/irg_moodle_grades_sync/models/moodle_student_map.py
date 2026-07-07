from odoo import models, fields


class IrgMoodleStudentMap(models.Model):
    _name = 'irg.moodle.student.map'
    _description = 'Resolución manual alumno Moodle -> alumno Odoo'
    _order = 'moodle_fullname'

    moodle_user_id = fields.Integer(
        string='ID usuario Moodle', required=True, index=True)
    moodle_fullname = fields.Char(string='Nombre en Moodle')
    moodle_email = fields.Char(string='Correo en Moodle')
    student_id = fields.Many2one(
        'op.student', string='Alumno Odoo', required=True, ondelete='cascade')

    _sql_constraints = [
        ('moodle_user_id_uniq', 'unique(moodle_user_id)',
         'Ya existe una resolución manual para este usuario de Moodle.'),
    ]
