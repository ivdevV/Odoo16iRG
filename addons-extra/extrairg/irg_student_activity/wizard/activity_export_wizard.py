# -*- coding: utf-8 -*-
from odoo import fields, models


class IrgStudentActivityExportWizard(models.TransientModel):
    _name = "irg.student.activity.export.wizard"
    _description = "Exportación CSV de actividad del alumno"

    student_id = fields.Many2one("op.student", string="Alumno", required=True)
    file_data = fields.Binary(string="CSV", readonly=True)
    filename = fields.Char(string="Nombre del archivo", readonly=True)
    state = fields.Selection(
        [("done", "Hecho")],
        default="done",
        string="Estado",
    )
