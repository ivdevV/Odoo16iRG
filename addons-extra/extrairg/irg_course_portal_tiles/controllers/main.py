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
        try:
            return request.render('irg_course_portal_tiles.tfm_page', {
                'course': course,
                'supervisors': supervisors,
                'documents': documents,
            })
        except Exception as e:
            # Fallback: log and render a safe alternative page
            from odoo import _
            _logger.exception('TFM page rendering failed for course %s', course_id)
            return request.render('irg_course_portal_tiles.tfm_page_fallback', {
                'course': course,
                'error': str(e),
            })

    @http.route(['/help'], type='http', auth='public', website=True)
    def help_page(self, **kwargs):
        return request.render('irg_course_portal_tiles.help_page', {})

    @http.route(['/help/chat'], type='json', auth='public', methods=['POST'])
    def help_chat(self, **kwargs):
        # Simple keyword-based chatbot for provisional support
        message = (kwargs.get('message') or '') if kwargs else ''
        text = message.lower()
        reply = "Lo siento, no he entendido tu consulta. Prueba: 'exámenes', 'tfm', 'factura', 'horario'."
        if 'examen' in text or 'exámenes' in text:
            reply = "Consulta el apartado 'Exámenes' en tu panel o contacta con tu tutor para fechas concretas."
        elif 'tfm' in text or 'trabajo fin' in text:
            reply = "Para el TFM, utiliza el enlace 'TFM' en la sección del curso para ver instrucciones y subir archivos."
        elif 'factura' in text or 'facturas' in text or 'pago' in text:
            reply = "Las facturas están disponibles en tu panel (tile 'Facturas'). Si falta alguna, contacta con administración."
        elif 'horario' in text or 'calendar' in text or 'calendario' in text:
            reply = "Puedes acceder al Calendario desde el tile 'Calendario' del curso o en la sección 'Mi agenda'."
        return {'reply': reply}
