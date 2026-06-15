# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class IrgDiplomadoRegistry(models.Model):
    _name = 'irg.diplomado.registry'
    _description = 'Registro de Diplomados'
    _order = 'issue_date desc, id desc'

    name = fields.Char(
        string='Número de Registro',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help=_("Número de registro único del diplomado.")
    )
    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        ondelete='restrict',
        help=_("Estudiante al que se le otorga el diplomado.")
    )
    student_name = fields.Char(
        string='Nombre del Alumno',
        required=True,
        help=_("Nombre completo del alumno en el momento de la expedición.")
    )
    course_id = fields.Many2one(
        'op.course',
        string='Curso',
        required=True,
        ondelete='restrict',
        help=_("Curso/Diplomado cursado.")
    )
    diplomado_name = fields.Char(
        string='Nombre del Diplomado',
        required=True,
        help=_("Nombre descriptivo del diplomado impreso.")
    )
    start_date = fields.Date(
        string='Fecha de Inicio',
        help=_("Fecha de inicio del curso.")
    )
    end_date = fields.Date(
        string='Fecha de Fin',
        help=_("Fecha de finalización del curso.")
    )
    duration_hours = fields.Integer(
        string='Duración (Horas)',
        help=_("Duración total del diplomado en horas.")
    )
    duration_ects = fields.Float(
        string='Créditos ECTS',
        help=_("Créditos ECTS asignados al diplomado.")
    )
    issue_date = fields.Date(
        string='Fecha de Expedición',
        default=fields.Date.context_today,
        required=True,
        help=_("Fecha en la que se expide/imprime el diplomado.")
    )
    diploma_type = fields.Selection([
        ('digital', 'Digital'),
        ('physical', 'Físico')
    ], string='Tipo de Diploma', required=True, default='digital', help=_("Tipo de diploma generado."))
    
    subjects_presencial = fields.Text(
        string='Asignaturas Presenciales',
        help=_("Listado de asignaturas presenciales que figurarán en el reverso.")
    )
    subjects_online = fields.Text(
        string='Asignaturas Online',
        help=_("Listado de asignaturas online que figurarán en el reverso.")
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('irg.diplomado.registry') or _('New')
        return super(IrgDiplomadoRegistry, self).create(vals)

    def action_reprint(self):
        self.ensure_one()
        report = self.env.ref('irg_generacion_diplomados.action_report_diplomado')
        return report.report_action(self)
