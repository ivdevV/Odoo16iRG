# -*- coding: utf-8 -*-
from odoo import fields, models


class IrgStudentActivityLine(models.TransientModel):
    _name = "irg.student.activity.line"
    _description = "Línea de actividad del alumno"
    _order = "event_datetime desc, id desc"

    student_id = fields.Many2one("op.student", required=True, ondelete="cascade")
    event_datetime = fields.Datetime(string="Fecha", readonly=True)
    event_type = fields.Selection(
        [("campus", "Campus"), ("evaluation", "Evaluación")],
        string="Tipo",
        readonly=True,
    )
    channel_name = fields.Char(string="Curso / canal", readonly=True)
    element_name = fields.Char(string="Elemento", readonly=True)
    detail = fields.Char(string="Detalle", readonly=True)
    result = fields.Char(string="Resultado", readonly=True)
    batch_code = fields.Char(string="Lote", readonly=True)
