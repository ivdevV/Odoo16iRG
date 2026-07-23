from odoo import api, fields, models


class IrgGradebookMoodleCourseMap(models.Model):
    _inherit = "irg.gradebook.moodle.course.map"

    irg_op_course_database_id = fields.Integer(
        string="ID curso Odoo", compute="_compute_irg_course_context"
    )
    irg_subject_map_ids = fields.One2many(
        "irg.gradebook.moodle.map", "course_map_id", string="Asignaturas Moodle"
    )
    irg_subject_map_count = fields.Integer(
        string="Asignaturas mapeadas", compute="_compute_irg_course_context"
    )

    @api.depends("op_course_id", "irg_subject_map_ids")
    def _compute_irg_course_context(self):
        for record in self:
            record.irg_op_course_database_id = record.op_course_id.id or 0
            record.irg_subject_map_count = len(record.irg_subject_map_ids)


class IrgGradebookMoodleMap(models.Model):
    _inherit = "irg.gradebook.moodle.map"

    irg_op_course_id = fields.Many2one(
        "op.course", related="course_map_id.op_course_id", readonly=True, store=True
    )
    irg_op_course_database_id = fields.Integer(
        string="ID curso Odoo", compute="_compute_irg_mapping_context"
    )
    irg_op_subject_database_id = fields.Integer(
        string="ID asignatura Odoo", compute="_compute_irg_mapping_context"
    )
    irg_op_subject_name = fields.Char(
        string="Nombre asignatura Odoo", related="op_subject_id.name", readonly=True
    )
    irg_op_subject_code = fields.Char(
        string="Código asignatura Odoo", related="op_subject_id.code", readonly=True
    )
    irg_activity_count = fields.Integer(
        string="N.º de actividades", compute="_compute_irg_mapping_context"
    )
    irg_activity_ids_display = fields.Char(
        string="Activity IDs", compute="_compute_irg_mapping_context"
    )

    @api.depends(
        "course_map_id.op_course_id", "op_subject_id", "line_ids.moodle_activity_id"
    )
    def _compute_irg_mapping_context(self):
        for record in self:
            record.irg_op_course_database_id = (
                record.course_map_id.op_course_id.id or 0
            )
            record.irg_op_subject_database_id = record.op_subject_id.id or 0
            activity_ids = record.line_ids.sorted("moodle_activity_id").mapped(
                "moodle_activity_id"
            )
            record.irg_activity_count = len(activity_ids)
            record.irg_activity_ids_display = ", ".join(map(str, activity_ids))
