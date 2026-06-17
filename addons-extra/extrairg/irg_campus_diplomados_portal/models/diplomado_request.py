# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class IrgDiplomadoRequest(models.Model):
    _name = 'irg.diplomado.request'
    _description = 'Solicitud de Expedición de Diplomado'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Código de Solicitud',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help=_("Código único de la solicitud de diplomado.")
    )
    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        ondelete='restrict',
        tracking=True,
        help=_("Estudiante que realiza la solicitud.")
    )
    course_id = fields.Many2one(
        'op.course',
        string='Curso/Diplomado',
        required=True,
        ondelete='restrict',
        tracking=True,
        help=_("Curso de tipo diplomado para el que se solicita la expedición.")
    )
    request_date = fields.Date(
        string='Fecha de Solicitud',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
        help=_("Fecha en la que se registra la solicitud desde el portal.")
    )
    state = fields.Selection([
        ('requested', 'Solicitado'),
        ('processed', 'Procesado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='requested', required=True, tracking=True, help=_("Estado de la solicitud."))
    
    diplomado_registry_id = fields.Many2one(
        'irg.diplomado.registry',
        string='Diploma Emitido',
        copy=False,
        readonly=True,
        tracking=True,
        help=_("Diploma de diplomado emitido vinculado a esta solicitud.")
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('irg.diplomado.request') or _('New')
        return super(IrgDiplomadoRequest, self).create(vals)
