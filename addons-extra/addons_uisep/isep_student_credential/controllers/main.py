from datetime import date
from odoo import http
from odoo.http import request, content_disposition
import base64
import logging

_logger = logging.getLogger(__name__)


class CredentialController(http.Controller):

    @http.route('/credential/view/<string:code>', type='http', auth='public', website=True)
    def view_student_credential(self, code, **kwargs):
        student = request.env['op.admission'].sudo().search([('application_number', '=', code)], limit=1)

        if not student:
            return request.render('isep_student_credential.student_not_found_template', {
                'code': code,
            })

        today = date.today()
        if not student.due_date or student.due_date < today:
            return request.render('isep_student_credential.student_expired_template', {
                'student': student,
            })

        return request.render('isep_student_credential.student_info_template', {
            'student': student,
        })

    
    @http.route('/credential/download/<int:application_number>', type='http', auth='public', website=True)
    def download_admission_credential_pdf(self, application_number, **kwargs):
        admission = request.env['op.admission'].sudo().browse(application_number)

        if not admission.exists():
            return request.not_found()

        pdf_content, _ = request.env['ir.actions.report']._render_qweb_pdf(
            'isep_student_credential.r_credential', [admission.id]
        )

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', f'attachment; filename=credencial_{admission.name}.pdf')
        ]

        return request.make_response(pdf_content, headers=headers)
        

    
    @http.route('/credential/download', type='http', auth='user', website=True)
    def download_my_credential(self, **kw):
        Admission = request.env['op.admission'].sudo()
        partner = request.env.user.partner_id

        admission = Admission.search(
            [('partner_id', '=', partner.id)],
            order='due_date desc, id desc',
            limit=1
        )
        if not admission:
            return request.not_found()

        pdf_content, _ = request.env['ir.actions.report']._render_qweb_pdf(
            'isep_student_credential.r_credential',
            [admission.id]
        )

        filename = 'credencial.pdf'
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Length', str(len(pdf_content))),
                ('Content-Disposition', content_disposition(filename))
            ]
        )

