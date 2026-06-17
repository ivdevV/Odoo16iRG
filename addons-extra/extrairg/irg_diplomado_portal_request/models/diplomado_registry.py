# -*- coding: utf-8 -*-
from odoo import api, models


class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'

    def _link_portal_diplomado_requests(self):
        Request = self.env['irg.diplomado.portal.request'].sudo()
        for record in self:
            request_record = Request.search([
                ('student_id', '=', record.student_id.id),
                ('course_id', '=', record.course_id.id),
                ('state', '=', 'requested'),
            ], order='id desc', limit=1)
            if request_record:
                request_record.write({
                    'diplomado_registry_id': record.id,
                    'state': 'processed',
                })

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._link_portal_diplomado_requests()
        return record

    def write(self, vals):
        result = super().write(vals)
        if {'student_id', 'course_id'} & set(vals):
            self._link_portal_diplomado_requests()
        return result
