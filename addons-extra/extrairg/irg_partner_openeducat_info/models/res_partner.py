# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    student_id = fields.Many2one(
        'op.student',
        compute='_compute_student_id',
        search='_search_student_id',
        string='Estudiante OpenEduCat',
    )

    # Campos de Información Educativa
    student_gr_no = fields.Char(
        related='student_id.gr_no',
        readonly=False,
        string='Nº de Registro / Matrícula',
    )
    student_file_closing_date = fields.Date(
        related='student_id.file_closing_date',
        readonly=False,
        string='Fecha cierre de expediente',
    )
    student_sepyc_program = fields.Boolean(
        related='student_id.sepyc_program',
        readonly=False,
        string='Programa Sepyc / Sep',
    )
    student_status = fields.Selection(
        related='student_id.status_student',
        readonly=True,
        string='Estado de estudiante',
    )
    student_total_completion_porc = fields.Float(
        related='student_id.total_completion_porc',
        readonly=True,
        string='Progreso Total',
    )
    student_op_admission_ids = fields.One2many(
        related='student_id.op_admission_ids',
        readonly=True,
        string='Admisión',
    )
    student_op_course_ids = fields.One2many(
        related='student_id.op_course_ids',
        readonly=True,
        string='Curso',
    )

    # Campos de Acceso
    student_login_date = fields.Datetime(
        related='student_id.login_date',
        readonly=True,
        string='Última autenticación',
    )
    student_login_line_ids = fields.One2many(
        related='student_id.login_line_ids',
        readonly=True,
        string='Historial de Accesos',
    )

    @api.depends()
    def _compute_student_id(self):
        for partner in self:
            student = self.env['op.student'].sudo().search([('partner_id', '=', partner.id)], limit=1)
            partner.student_id = student.id if student else False

    def _search_student_id(self, operator, value):
        students = self.env['op.student'].sudo().search([('id', operator, value)])
        return [('id', 'in', students.mapped('partner_id').ids)]
