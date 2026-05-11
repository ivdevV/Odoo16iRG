# -*- coding: utf-8 -*-

import base64
import os

from odoo import _
from odoo.http import Controller, request, route


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}


class ScholarshipDocumentsPortal(Controller):
    def _get_current_partner(self):
        user = request.env.user
        # Portal users need to resolve their linked OpenEduCat student even when
        # they do not have direct read access to op.student records.
        student = request.env['op.student'].sudo().search([
            '|',
            ('user_id', '=', user.id),
            ('partner_id', '=', user.partner_id.id),
        ], limit=1)
        return student.partner_id if student else user.partner_id

    def _prepare_portal_values(self, partner, error=None, success=False):
        # The partner is explicitly derived from the authenticated user above;
        # sudo keeps the portal page usable while record rules still protect downloads.
        documents = request.env['irg.scholarship.document'].sudo().search([
            ('partner_id', '=', partner.id),
        ])
        return {
            'partner': partner,
            'scholarship_type': partner.irg_scholarship_type_id,
            'documents': documents,
            'allowed_extensions': ', '.join(sorted(ALLOWED_EXTENSIONS)),
            'max_file_size_mb': int(MAX_FILE_SIZE_BYTES / 1024 / 1024),
            'error': error,
            'success': success,
        }

    def _render_portal_page(self, error=None, success=False):
        partner = self._get_current_partner()
        return request.render(
            'irg_student_scholarship_documents.portal_scholarship_documents',
            self._prepare_portal_values(partner, error=error, success=success),
        )

    @route('/my/scholarship-documents', type='http', auth='user', website=True)
    def scholarship_documents_page(self, **kwargs):
        return self._render_portal_page(success=kwargs.get('success') == '1')

    @route(
        '/my/scholarship-documents/upload',
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def scholarship_documents_upload(self, **kwargs):
        partner = self._get_current_partner()
        upload = request.httprequest.files.get('scholarship_file')
        if not upload:
            return self._render_portal_page(error=_('Selecciona un archivo.'))

        filename = (upload.filename or '').strip()
        if not filename:
            return self._render_portal_page(error=_('El archivo no tiene nombre.'))

        extension = os.path.splitext(filename)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return self._render_portal_page(
                error=_('Formato no permitido. Usa PDF, JPG, PNG, DOC o DOCX.')
            )

        content = upload.read()
        if not content:
            return self._render_portal_page(error=_('El archivo esta vacio.'))
        if len(content) > MAX_FILE_SIZE_BYTES:
            return self._render_portal_page(error=_('El archivo supera el limite de 10 MB.'))

        document_name = (kwargs.get('document_name') or filename).strip()
        note = (kwargs.get('note') or '').strip()

        # Creation is intentionally sudoed after validating the authenticated
        # user's partner, because portal users cannot create binary attachments directly.
        request.env['irg.scholarship.document'].sudo().create({
            'partner_id': partner.id,
            'name': document_name,
            'filename': filename,
            'file': base64.b64encode(content),
            'note': note,
        })
        return request.redirect('/my/scholarship-documents?success=1')
