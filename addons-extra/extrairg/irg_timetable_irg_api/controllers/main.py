# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class IrgTimetableApiController(http.Controller):
    """Resolves the IRG API lote name for the current portal student."""

    _DEFAULT_BASE_URL = 'https://calendario.institutoraimongaja.com'

    def _resolve_lote(self, stud_id=None):
        """
        Return (lote_name, base_url) for the given student (or the current user).

        Lookup priority (first non-empty wins):
        1. op.student.course_detail_ids with state='running' → batch_id.name
        2. res.users.op_batch_ids → first active batch.name
        3. op.student.course (separate model) → batch_id.name
        4. op.admission → batch_id.name
        """
        env = request.env

        # --- Resolve student record ---
        if stud_id:
            student = env['op.student'].sudo().search(
                [('id', '=', int(stud_id))], limit=1
            )
        else:
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

        # 1. course_detail_ids (most reliable — direct enrollment record)
        running = student.course_detail_ids.filtered(
            lambda r: r.state == 'running' and r.batch_id
        )
        if running:
            return running[0].batch_id.name, base_url

        # 2. res.users.op_batch_ids (direct user→batch assignment)
        user = env['res.users'].sudo().search(
            [('partner_id', '=', student.partner_id.id)], limit=1
        )
        if user and 'op_batch_ids' in user._fields:
            active_batches = user.op_batch_ids.filtered('active')
            if active_batches:
                return active_batches[0].name, base_url

        # 3. op.student.course (separate model, any state)
        StudentCourse = env['op.student.course'].sudo()
        if 'batch_id' in StudentCourse._fields:
            sc = StudentCourse.search(
                [('student_id', '=', student.id), ('batch_id', '!=', False)],
                limit=1,
            )
            if sc:
                return sc.batch_id.name, base_url

        # 4. op.admission
        Admission = env['op.admission'].sudo()
        if 'batch_id' in Admission._fields:
            adm = Admission.search(
                [
                    ('partner_id', '=', student.partner_id.id),
                    ('batch_id', '!=', False),
                ],
                limit=1,
            )
            if adm:
                return adm.batch_id.name, base_url

        return None, base_url

    @http.route('/irg-timetable/lote', type='json', auth='user', website=True)
    def get_lote(self, stud_id=None, **kwargs):
        """
        Returns:
            { "lote": "MOPIHC2601", "base_url": "https://..." }
        or on failure:
            { "lote": null, "base_url": "https://...", "error": "no_batch" }
        """
        lote, base_url = self._resolve_lote(stud_id=stud_id)
        if not lote:
            return {'lote': None, 'base_url': base_url, 'error': 'no_batch'}
        return {'lote': lote, 'base_url': base_url}
