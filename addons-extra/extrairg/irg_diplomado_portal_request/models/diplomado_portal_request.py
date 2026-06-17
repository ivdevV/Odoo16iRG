# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrgDiplomadoPortalRequest(models.Model):
    _name = 'irg.diplomado.portal.request'
    _description = 'Solicitud Portal de Diploma de Diplomado'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Codigo de Solicitud',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    student_id = fields.Many2one('op.student', string='Alumno', required=True, ondelete='restrict', tracking=True)
    partner_id = fields.Many2one('res.partner', related='student_id.partner_id', string='Contacto', store=True, readonly=True)
    course_id = fields.Many2one('op.course', string='Diplomado', required=True, ondelete='restrict', tracking=True)
    gradebook_student_id = fields.Many2one(
        'app.gradebook.student',
        string='Libreta Academica',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    final_grade = fields.Float(string='Calificacion Final', digits=(16, 2), required=True, tracking=True)
    request_date = fields.Date(string='Fecha de Solicitud', default=fields.Date.context_today, required=True, tracking=True)
    state = fields.Selection([
        ('requested', 'Solicitado'),
        ('processed', 'Procesado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='requested', required=True, tracking=True)
    diplomado_registry_id = fields.Many2one(
        'irg.diplomado.registry',
        string='Diploma Emitido',
        copy=False,
        readonly=True,
        tracking=True,
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('irg.diplomado.portal.request') or _('New')
        return super().create(vals)

    @api.constrains('course_id', 'gradebook_student_id', 'final_grade', 'state')
    def _check_diplomado_eligibility(self):
        for record in self.filtered(lambda req: req.state != 'cancelled'):
            if not record.course_id.irg_is_diplomado():
                raise ValidationError(_('Solo se pueden solicitar diplomas para cursos de tipo diplomado.'))
            if record.gradebook_student_id.course_id != record.course_id:
                raise ValidationError(_('La libreta academica no pertenece al diplomado solicitado.'))
            if record.gradebook_student_id.state != 'done':
                raise ValidationError(_('El diplomado debe estar completado para solicitar el diploma.'))
            if record.final_grade <= 7.0:
                raise ValidationError(_('La calificacion final debe ser superior a 7.0.'))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
