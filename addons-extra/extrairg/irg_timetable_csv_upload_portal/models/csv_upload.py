# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class IrgTimetableCsvUpload(models.Model):
    """Registro de uploads de CSV de calendarios académicos."""

    _name = 'irg.timetable.csv.upload'
    _description = 'Upload de CSV - Calendarios Académicos'
    _order = 'upload_date desc'

    name = fields.Char(
        string=_('Nombre del archivo'),
        required=True,
        readonly=True,
    )
    upload_date = fields.Datetime(
        string=_('Fecha de upload'),
        default=fields.Datetime.now,
        readonly=True,
    )
    uploaded_by = fields.Many2one(
        'res.users',
        string=_('Subido por'),
        default=lambda self: self.env.user,
        readonly=True,
    )
    file_size = fields.Integer(
        string=_('Tamaño (bytes)'),
        readonly=True,
    )
    state = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('processing', 'Procesando'),
            ('done', '✓ Completado'),
            ('error', '✗ Error'),
        ],
        string=_('Estado'),
        default='pending',
        readonly=True,
    )
    error_message = fields.Text(
        string=_('Mensaje de error'),
        readonly=True,
    )
    import_log_id = fields.Many2one(
        'irg.timetable.import.log',
        string=_('Log de importación generado'),
        readonly=True,
        ondelete='set null',
    )

    _sql_constraints = [
        ('unique_name_date', 'unique(name, upload_date)', 
         'Solo puede haber un upload por archivo y fecha'),
    ]

    def action_view_import_log(self):
        """Abre el log de importación asociado."""
        if self.import_log_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'irg.timetable.import.log',
                'res_id': self.import_log_id.id,
                'view_mode': 'form',
            }
        return False
