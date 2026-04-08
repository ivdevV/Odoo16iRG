# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

from odoo.addons.irg_timetable_irg_api.controllers.main import IrgTimetableApiController

_logger = logging.getLogger(__name__)


class IrgTimetableLoteBatchFix(IrgTimetableApiController):
    """
    Extiende el endpoint /irg-timetable/lote para aceptar un batch_id explícito.

    Cuando la URL del portal incluye ?batch_id=X (ej. /student/timetable/?batch_id=14055),
    el JS pasa ese valor aquí y se resuelve el nombre del lote directamente desde
    op.batch, sin pasar por la lógica de enrollment que puede devolver el lote
    incorrecto para alumnos con múltiples programas.

    Si no se proporciona batch_id, delega al comportamiento original del módulo
    irg_timetable_irg_api (resolución por course_id o primer enrollment running).
    """

    @http.route('/irg-timetable/lote', type='json', auth='user', website=True)
    def get_lote(self, course_id=None, batch_id=None, **kwargs):
        if batch_id:
            try:
                batch = request.env['op.batch'].sudo().browse(int(batch_id))
                if batch.exists() and batch.name:
                    base_url = (
                        request.env['ir.config_parameter'].sudo().get_param(
                            'irg_calendarios.api_base_url',
                            default=self._DEFAULT_BASE_URL,
                        ).rstrip('/') or self._DEFAULT_BASE_URL
                    )
                    _logger.debug(
                        'IRG LOTE BATCH FIX: batch_id=%s → lote=%s',
                        batch_id, batch.name,
                    )
                    return {'lote': batch.name, 'base_url': base_url}
            except Exception:
                _logger.warning(
                    'IRG LOTE BATCH FIX: no se pudo resolver batch_id=%s, '
                    'usando fallback', batch_id, exc_info=True,
                )
        # Sin batch_id o si falló: comportamiento original
        return super().get_lote(course_id=course_id, **kwargs)
