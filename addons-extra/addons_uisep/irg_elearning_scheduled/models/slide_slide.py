from odoo import models, fields, api
from datetime import date

class Slide(models.Model):
    _inherit = 'slide.slide'

    scheduled_date = fields.Date(
        string='Fecha de Disponibilidad',
        help='El contenido no estará disponible hasta esta fecha. Dejar vacío para acceso inmediato.'
    )

    is_available_by_date = fields.Boolean(
        compute='_compute_is_available_by_date',
        string='Disponible por Fecha'
    )

    @api.depends('scheduled_date')
    def _compute_is_available_by_date(self):
        today = date.today()
        for slide in self:
            if not slide.scheduled_date:
                slide.is_available_by_date = True
            else:
                slide.is_available_by_date = today >= slide.scheduled_date
