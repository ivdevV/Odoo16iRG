# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request
from odoo.addons.irg_campus_diplomados_portal.controllers.portal import IrgCampusDiplomadosPortal
from odoo.addons.irg_diplomado_portal_request.controllers.portal import IrgDiplomadoPortalRequestController

_logger = logging.getLogger(__name__)


class IrgDiplomadoPortalRequestClassStart(IrgDiplomadoPortalRequestController):

    @http.route()
    def request_diplomado(self, course_id, **post):
        return super().request_diplomado(course_id, **post)

    @http.route()
    def download_diplomado(self, registry_id, **kw):
        return super().download_diplomado(registry_id, **kw)

    def _create_diplomado_registry(self, student, course, gradebook):
        registry = super()._create_diplomado_registry(student, course, gradebook)
        batch = gradebook.batch_id if gradebook else False
        start = registry._irg_celebration_start_from_batch(batch)
        if start and registry.start_date != start:
            registry.start_date = start
        return registry

    def _send_diplomado_file(self, diplomado):
        try:
            if diplomado._irg_should_refresh_on_download():
                diplomado.action_reprint()
        except Exception:
            _logger.exception(
                'Error al regenerar el PDF del diplomado %s', diplomado.id
            )
            return request.redirect(
                '/campus/diplomados/%s?error=no_pdf' % diplomado.course_id.id
            )
        return super()._send_diplomado_file(diplomado)


class IrgCampusDiplomadosClassStart(IrgCampusDiplomadosPortal):

    @http.route()
    def download_diplomado(self, diplomado_id, **kw):
        partner = request.env.user.partner_id
        diplomado = request.env['irg.diplomado.registry'].sudo().browse(diplomado_id)
        # Same partner + grade gate as the parent controller, applied before
        # mutating an issued PDF. Copied on purpose so a later parent change
        # must be mirrored here.
        if (
            diplomado.exists()
            and diplomado.student_id.partner_id.id == partner.id
        ):
            gradebook = request.env['app.gradebook.student'].sudo().search([
                ('student_id', '=', diplomado.student_id.id),
                ('course_id', '=', diplomado.course_id.id),
            ], limit=1)
            if gradebook and gradebook.total_final > 7.0:
                try:
                    if diplomado._irg_should_refresh_on_download():
                        diplomado.action_reprint()
                except Exception:
                    # Keep the previous PDF (fail-closed) and let the parent
                    # stream it; do not clear attachment_id.
                    _logger.exception(
                        'Error al regenerar el PDF del diplomado %s', diplomado_id
                    )
        return super().download_diplomado(diplomado_id, **kw)
