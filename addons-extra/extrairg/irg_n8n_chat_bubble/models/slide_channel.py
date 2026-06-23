# -*- coding: utf-8 -*-
from odoo import models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def irg_get_n8n_chat_config(self):
        """Retorna la configuración de la burbuja de chat de n8n para este canal.

        Busca entre los cursos de OpenEduCat asociados a este canal de eLearning.
        Si alguno tiene activo el chat de n8n con una URL de webhook configurada,
        retorna los datos del widget y la metadata contextual del estudiante.
        """
        self.ensure_one()
        user = self.env.user
        partner = user.partner_id if user else False

        # Obtener los cursos relacionados utilizando el método de convocatorias_v2
        related_courses = self._irg_get_related_courses()

        active_course = False
        for course in related_courses:
            if course.irg_n8n_chat_enabled and course.irg_n8n_chat_webhook_url:
                active_course = course
                break

        if active_course:
            return {
                'enabled': True,
                'webhook_url': active_course.irg_n8n_chat_webhook_url.strip(),
                'title': active_course.irg_n8n_chat_title or 'Soporte Académico',
                'welcome_msg': active_course.irg_n8n_chat_welcome_msg or '¡Hola! ¿En qué te puedo ayudar hoy?',
                'student_name': partner.name if partner else 'Estudiante Invitado',
                'student_email': partner.email if partner else '',
                'course_name': active_course.name,
                'subject_name': self.name,
            }

        return {'enabled': False}
