# -*- coding: utf-8 -*-

from odoo import fields, models


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    irg_practice_center_type_id = fields.Many2one(
        'practice.center.type',
        string='Modalidad de prácticas',
        tracking=True,
        help='Tipo de prácticas de esta matrícula. Lo rellena la última '
             'solicitud aprobada o posterior y secretaría puede corregirlo.',
    )

    def init(self):
        # Installing this inherit re-checks FKs on op.student.course. Beta has
        # no student_id FK today, so Odoo tries to add ON DELETE CASCADE and
        # fails if any enrollment points at a deleted op.student.
        self.env.cr.execute("""
            UPDATE op_student_course AS osc
               SET student_id = NULL
             WHERE osc.student_id IS NOT NULL
               AND NOT EXISTS (
                    SELECT 1 FROM op_student AS student
                    WHERE student.id = osc.student_id
               )
        """)
