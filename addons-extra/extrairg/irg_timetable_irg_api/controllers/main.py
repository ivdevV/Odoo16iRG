# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class IrgTimetableApiController(http.Controller):
    """Resolves the IRG API lote for the current portal student and course."""

    _DEFAULT_BASE_URL = 'https://calendario.institutoraimongaja.com'

    def _resolve_lote(self, course_id=None):
        """
        Return (lote_name, base_url) for the current user and the given op.course id.

        Looks up op.student.course where student matches the logged-in user
        and course_id matches the course being viewed.
        Falls back to the first running enrollment if no course_id is given.
        """
        env = request.env

        student = env['op.student'].sudo().search(
            [('user_id', '=', env.uid)], limit=1
        )

        base_url = (
            env['ir.config_parameter'].sudo().get_param(
                'irg_calendarios.api_base_url', default=self._DEFAULT_BASE_URL
            ).rstrip('/')
            or self._DEFAULT_BASE_URL
        )

        if not student:
            return None, base_url

        domain = [('student_id', '=', student.id), ('batch_id', '!=', False)]
        if course_id:
            domain.append(('course_id', '=', int(course_id)))
        else:
            domain.append(('state', '=', 'running'))

        enrollment = env['op.student.course'].sudo().search(domain, order='id desc', limit=1)
        if enrollment:
            return enrollment.batch_id.name, base_url

        # Fallback: any enrollment without state filter
        if course_id:
            enrollment = env['op.student.course'].sudo().search(
                [('student_id', '=', student.id), ('course_id', '=', int(course_id)), ('batch_id', '!=', False)],
                order='id desc', limit=1
            )
            if enrollment:
                return enrollment.batch_id.name, base_url

        return None, base_url

    @http.route('/irg-timetable/lote', type='json', auth='user', website=True)
    def get_lote(self, course_id=None, **kwargs):
        """
        Returns:
            { "lote": "MOPIHC2601", "base_url": "https://..." }
        or on failure:
            { "lote": null, "base_url": "https://...", "error": "no_batch" }
        """
        lote, base_url = self._resolve_lote(course_id=course_id)
        if not lote:
            return {'lote': None, 'base_url': base_url, 'error': 'no_batch'}
        return {'lote': lote, 'base_url': base_url}
