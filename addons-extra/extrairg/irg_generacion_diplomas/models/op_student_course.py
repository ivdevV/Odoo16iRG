from odoo import models

class OpStudentCourse(models.Model):
    _inherit = "op.student.course"

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.course_id.name} ({record.batch_id.name})"
            result.append((record.id, name))
        return result
