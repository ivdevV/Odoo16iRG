from odoo import fields, models, _


class IrgCourseModality(models.Model):
    _name = 'irg.course.modality'
    _description = 'Modalidad de Curso'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Código',
        required=True,
        size=32,
        help='Código técnico. Ejemplo: presencial, homeclass, online',
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )
    course_ids = fields.Many2many(
        'op.course',
        'op_course_irg_modality_rel',
        'modality_id',
        'course_id',
        string='Cursos',
    )

    _sql_constraints = [
        (
            'code_uniq',
            'UNIQUE(code)',
            _('Ya existe una modalidad con ese código.'),
        ),
    ]
