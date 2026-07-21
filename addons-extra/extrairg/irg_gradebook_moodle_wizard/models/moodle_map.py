from odoo import fields, models


class IrgGradebookMoodleMap(models.Model):
    _name = 'irg.gradebook.moodle.map'
    _description = 'Mapeo asignatura Odoo -> actividades Moodle (libreta)'
    _order = 'op_subject_id'
    _rec_name = 'op_subject_id'

    op_subject_id = fields.Many2one(
        'op.subject', string='Asignatura Odoo', required=True, index=True,
        ondelete='cascade')
    moodle_course_id = fields.Integer(
        string='ID curso Moodle', required=True, index=True)
    moodle_course_name = fields.Char(string='Curso Moodle')
    line_ids = fields.One2many(
        'irg.gradebook.moodle.map.line', 'map_id', string='Actividades')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('subject_course_uniq', 'unique(op_subject_id, moodle_course_id)',
         'Ya existe un mapeo para esta asignatura y curso de Moodle.'),
    ]


class IrgGradebookMoodleMapLine(models.Model):
    _name = 'irg.gradebook.moodle.map.line'
    _description = 'Actividad Moodle mapeada a una asignatura'
    _order = 'map_id, moodle_activity_id'

    map_id = fields.Many2one(
        'irg.gradebook.moodle.map', required=True, ondelete='cascade')
    moodle_activity_id = fields.Integer(
        string='ID actividad Moodle', required=True, index=True)
    name = fields.Char(string='Nombre actividad')
    activity_type = fields.Selection(
        [('quiz', 'Quiz'), ('assign', 'Tarea')],
        string='Tipo', default='quiz', required=True)
