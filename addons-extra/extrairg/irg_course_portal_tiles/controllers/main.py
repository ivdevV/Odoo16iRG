from odoo import http
from odoo.http import request


class IrgTFMController(http.Controller):
    @http.route(['/campus/course/<int:course_id>/tfm'], type='http', auth='user', website=True)
    def tfm_page(self, course_id, **kwargs):
        Course = request.env['op.course'].sudo()
        course = Course.browse(course_id)
        # try to get supervisors if the field exists, otherwise empty recordset
        try:
            supervisors = course.supervisor_ids
        except Exception:
            supervisors = request.env['res.partner'].sudo().browse([])
        # attachments linked to the course (TFM files)
        documents = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'op.course'),
            ('res_id', '=', course_id),
        ], order='create_date desc')
        return request.render('irg_course_portal_tiles.tfm_page', {
            'course': course,
            'supervisors': supervisors,
            'documents': documents,
        })
