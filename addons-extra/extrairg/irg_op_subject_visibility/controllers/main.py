# -*- coding: utf-8 -*-
from datetime import date

from odoo import http
from odoo.http import request

from odoo.addons.isep_elearning_custom.controllers.main import CustomWebsiteSlides


class SubjectVisibilitySlides(CustomWebsiteSlides):
    """Extiende el controlador de canales de eLearning para restringir el acceso
    a canales vinculados a asignaturas según la configuración de visibilidad por lote.

    La cadena de herencia de controladores es:
        WebsiteSlides (website_slides)
            ↳ CustomWebsiteSlides (isep_elearning_custom)
                ↳ SubjectVisibilitySlides (irg_op_subject_visibility)  ← este módulo

    La comprobación de visibilidad se realiza DESPUÉS de la comprobación de fecha de
    lote del módulo padre, por lo que si el lote ya ha expirado el usuario será
    redirigido antes de llegar a esta lógica.
    """

    @http.route([
        '/slides/<model("slide.channel"):channel>',
        '/slides/<model("slide.channel"):channel>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=CustomWebsiteSlides.sitemap_slide)
    def channel(self, channel, category=None, tag=None, page=1, slide_category=None,
                uncategorized=False, sorting=None, search=None, **kw):

        is_internal_user = request.env.user.has_group('base.group_user')
        if not is_internal_user:
            redirect = self._check_subject_visibility(channel)
            if redirect:
                return redirect

        return super().channel(
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
        """Comprueba si el canal eLearning es accesible para el lote activo del estudiante.

        Si la asignatura vinculada al canal está configurada con visibilidad restringida
        y el lote activo del estudiante no tiene acceso, redirige a la página de aviso.

        :param channel: registro de slide.channel
        :raises werkzeug.exceptions.HTTPException: redirección 303 si no tiene acceso
        """
        # Buscar la asignatura vinculada a este canal (campo añadido por isep_elearning_custom)
        Subject = request.env['op.subject'].sudo()
        subject = Subject.search([('slide_channel_id', '=', channel.id)], limit=1)

        if not subject:
            # Sin asignatura vinculada → sin restricción adicional
            return

        if subject.visible_all_course_batches:
            # Visibilidad general activa → sin restricción adicional
            return

        # Obtener el lote activo del estudiante (el de mayor fecha de fin que siga vigente)
        partner = request.env.user.partner_id
        today = date.today()
        admissions = request.env['op.admission'].sudo().search(
            [('partner_id', '=', partner.id)]
        )

        active_batch = False
        highest_end_date = False
        for admission in admissions:
            batch = admission.batch_id
            if not batch or not batch.end_date:
                continue
            if batch.end_date >= today:
                if not highest_end_date or batch.end_date > highest_end_date:
                    highest_end_date = batch.end_date
                    active_batch = batch

        if not active_batch:
            # Sin lote activo: sin datos suficientes para evaluar → permitir acceso
            # (la comprobación de expiración ya la hace el controlador padre)
            return

        if not subject.is_visible_for_batch(active_batch):
            return request.redirect(
                '/warning/subject-visibility/%s' % channel.id
            )

    # ------------------------------------------------------------------
    # Ruta de aviso de visibilidad restringida por asignatura
    # ------------------------------------------------------------------

    @http.route(
        '/warning/subject-visibility/<int:channel_id>',
        type='http',
        methods=['GET'],
        auth='user',
        website=True,
    )
    def subject_not_visible_warning(self, channel_id, **kw):
        """Página de aviso cuando una asignatura no es visible para el lote del estudiante."""
        channel = request.env['slide.channel'].sudo().browse(channel_id)
        subject = request.env['op.subject'].sudo().search(
            [('slide_channel_id', '=', channel_id)], limit=1
        )
        return request.render(
            'irg_op_subject_visibility.template_subject_not_visible',
            {
                'channel_name': channel.name if channel.exists() else '',
                'subject_name': subject.name if subject else '',
            }
        )
