import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


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
            return request.render('irg_course_portal_tiles.tfm_page_v2', {
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

    def _get_open_tickets_domain_for_current_user(self):
        partner = request.env.user.partner_id
        if not partner:
            return [('id', '=', False)]
        return [
            ('partner_id', '=', partner.id),
            ('stage_id.fold', '=', False),
        ]

    def _get_open_tickets_for_current_user(self, limit=10):
        domain = self._get_open_tickets_domain_for_current_user()
        return request.env['helpdesk.ticket'].search(domain, order='create_date desc', limit=limit)

    @http.route(['/help'], type='http', auth='user', website=True)
    def help_page(self, **kwargs):
        domain = self._get_open_tickets_domain_for_current_user()
        tickets = self._get_open_tickets_for_current_user(limit=10)
        total_open_tickets = request.env['helpdesk.ticket'].search_count(domain)
        return request.render('irg_course_portal_tiles.helpdesk_page', {
            'open_tickets': tickets,
            'has_more_open_tickets': total_open_tickets > len(tickets),
        })

    @http.route(['/helpdesk/atencion-al-cliente-1'], type='http', auth='user', website=True)
    def helpdesk_custom(self, **kwargs):
        domain = self._get_open_tickets_domain_for_current_user()
        tickets = self._get_open_tickets_for_current_user(limit=10)
        total_open_tickets = request.env['helpdesk.ticket'].search_count(domain)
        return request.render('irg_course_portal_tiles.helpdesk_page', {
            'open_tickets': tickets,
            'has_more_open_tickets': total_open_tickets > len(tickets),
        })

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
