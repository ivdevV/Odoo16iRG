from odoo import http
from odoo.http import request, content_disposition


class IrgTimetablePdfController(http.Controller):

    @http.route(['/student/timetable/pdf', '/student/timetable/<int:student_id>/pdf'], type='http', auth='user', website=True)
    def student_timetable_pdf(self, student_id=None, **kwargs):
        Student = request.env['op.student'].sudo()

        if student_id:
            student = Student.browse(student_id)
            if not student.exists():
                return request.not_found()

            current_partner = request.env.user.partner_id
            is_owner = student.partner_id.id == current_partner.id
            parent_partner_ids = student.parent_ids.mapped('user_id.partner_id').ids
            is_parent = current_partner.id in parent_partner_ids
            if not (is_owner or is_parent):
                return request.not_found()
        else:
            student = Student.search([('user_id', '=', request.env.uid)], limit=1)

        if not student:
            return request.not_found()

        report_service = request.env['ir.actions.report'].sudo().with_context(tz='Europe/Madrid')
        pdf_content, _ = report_service._render_qweb_pdf(
            'irg_timetable_pdf_export.report_student_timetable_pdf',
            student.ids,
        )

        filename = f"Calendario_{(student.name or 'estudiante').replace(' ', '_')}.pdf"
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', content_disposition(filename)),
        ]
        return request.make_response(pdf_content, headers=headers)
