# -*- coding: utf-8 -*-
from datetime import date

from odoo import http
from odoo.http import request
from odoo.addons.irg_course_convocatorias_v2.controllers.main import CourseConvocatoriasSlides
from odoo.addons.website_slides.controllers.main import WebsiteSlides


class OnlineSubjectVisibilitySlides(CourseConvocatoriasSlides):

    @http.route([
        '/slides/<model("slide.channel"):channel>',
        '/slides/<model("slide.channel"):channel>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=WebsiteSlides.sitemap_slide)
    def channel(self, channel, category=None, tag=None, page=1, slide_category=None,
                uncategorized=False, sorting=None, search=None, **kw):
        """Sobrescribe el controlador de canales para omitir la comprobación de fecha
        global obsoleta de CustomWebsiteSlides para cursos online que son válidos.
        """
        is_internal_user = request.env.user.has_group('base.group_user')
        if not is_internal_user:
            # Case 1: Channel is HomeClass and student is Online modality
            if channel.irg_online_channel_id:
                if channel._irg_is_online_student_for_channel():
                    return request.redirect('/slides/%s' % channel.irg_online_channel_id.id)

            # Case 2: Channel is Online clone and student is NOT Online modality (meaning HomeClass)
            elif channel.irg_homeclass_channel_id:
                if not channel.irg_homeclass_channel_id._irg_is_online_student_for_channel():
                    return request.redirect('/slides/%s' % channel.irg_homeclass_channel_id.id)

            # If no clone redirection occurred and there is a subject linked to the channel
            subject = request.env['op.subject'].sudo().search([('slide_channel_id', '=', channel.id)], limit=1)
            if subject:
                redirect = self._check_subject_visibility(channel)
                if redirect:
                    return redirect
                # Si la verificación de visibilidad de la asignatura es correcta (None)
                # y existe asignatura vinculada, llamamos directamente a WebsiteSlides.channel
                # puenteando a CustomWebsiteSlides.
                return WebsiteSlides.channel(
                    self,
                    channel,
                    category=category,
                    tag=tag,
                    page=page,
                    slide_category=slide_category,
                    uncategorized=uncategorized,
                    sorting=sorting,
                    search=search,
                    **kw
                )

        return super(OnlineSubjectVisibilitySlides, self).channel(
            channel,
            category=category,
            tag=tag,
            page=page,
            slide_category=slide_category,
            uncategorized=uncategorized,
            sorting=sorting,
            search=search,
            **kw
        )

    def _check_subject_visibility(self, channel):
        """Comprueba si el canal eLearning es accesible para el lote activo del estudiante,
        aplicando también la restricción de vencimiento por due_date para cursos online.
        """
        # Buscar la asignatura vinculada a este canal
        Subject = request.env['op.subject'].sudo()
        subject = Subject.search([('slide_channel_id', '=', channel.id)], limit=1)

        if not subject:
            # Sin asignatura vinculada → sin restricción adicional
            return None

        # Para todos los demás casos, comprobamos las admisiones del estudiante
        partner = request.env.user.partner_id
        today = date.today()
        course_ids = (subject.course_id + subject.course_ids).ids
        admissions = request.env['op.admission'].sudo().search([
            ('partner_id', '=', partner.id),
            ('course_id', 'in', course_ids)
        ])

        if not admissions:
            return request.redirect('/warning/subject-visibility/%s' % channel.id)

        expired_online_admissions = []
        has_online_admission = False

        for admission in admissions:
            if admission.irg_has_online_subject_opening_context():
                has_online_admission = True
                # Comprobar vencimiento por due_date
                if admission.due_date and today > admission.due_date:
                    expired_online_admissions.append(admission)
                    continue

                # Si no está expirado, comprobar visibilidad general
                if subject.visible_all_course_batches:
                    return None

                # Si no es general, comprobar ventana de apertura individual
                visible_subjects = admission.irg_get_visible_online_subjects_for_date(today)
                if subject in visible_subjects:
                    return None
            else:
                # Admisión estándar (por lote)
                if subject.visible_all_course_batches:
                    return None

                batch = admission.batch_id
                if batch and batch.end_date and batch.end_date >= today:
                    if subject.is_visible_for_batch(batch):
                        return None

        # Si llegamos aquí sin haber retornado None, el acceso está denegado.
        if has_online_admission and expired_online_admissions:
            # Redirigir a la página de aviso por vencimiento de curso online
            return request.redirect('/warning/online_admission/%s' % expired_online_admissions[0].id)

        # En cualquier otro caso, redirigir a aviso de visibilidad de asignatura estándar
        return request.redirect('/warning/subject-visibility/%s' % channel.id)


class OnlineWarningAdmissionController(http.Controller):

    @http.route(
        '/warning/online_admission/<int:admission_id>',
        type='http',
        methods=['GET'],
        auth='user',
        website=True,
    )
    def online_admission_expired_warning(self, admission_id, **kw):
        """Página de aviso cuando un curso online ha expirado (fecha de vencimiento superada)."""
        admission = request.env['op.admission'].sudo().browse(admission_id)
        is_internal_user = request.env.user.has_group('base.group_user')
        if not is_internal_user and (not admission.exists() or admission.partner_id != request.env.user.partner_id):
            return request.redirect('/my/home')

        return request.render(
            'irg_online_subject_portal_visibility.template_online_admission_expired',
            {
                'admission': admission,
                'course_name': admission.course_id.name if admission.course_id else '',
                'due_date': admission.due_date,
            }
        )
