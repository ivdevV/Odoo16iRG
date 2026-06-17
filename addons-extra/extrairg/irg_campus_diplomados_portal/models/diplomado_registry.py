# -*- coding: utf-8 -*-
from odoo import models, api

class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'

    @api.model
    def create(self, vals):
        record = super(IrgDiplomadoRegistry, self).create(vals)
        
        # Buscar solicitudes pendientes de diplomado para este estudiante y curso
        solicitud = self.env['irg.diplomado.request'].sudo().search([
            ('student_id', '=', record.student_id.id),
            ('course_id', '=', record.course_id.id),
            ('state', '=', 'requested')
        ], limit=1)
        
        if solicitud:
            solicitud.write({
                'diplomado_registry_id': record.id,
                'state': 'processed'
            })
            
        return record
