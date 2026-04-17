from odoo import http
from odoo.addons.irg_elearning_restrictions.controllers.main import WebsiteSlidesCustom
from odoo.http import request
from datetime import date


class WebsiteSlidesBatchRestrictions(WebsiteSlidesCustom):
    @http.route(['/slides/slide/<model("slide.slide"):slide>'], type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        # Verificar fecha programada
        if slide.scheduled_date:
            today = date.today()
            if today < slide.scheduled_date:
                return request.render('irg_elearning_scheduled.slide_scheduled_error', {
                    'slide': slide,
                    'scheduled_date': slide.scheduled_date,
                })

        # Verificar restricción por lote
        if slide.sudo().allowed_batch_ids:
            user = request.env.user
            if user._is_public():
                return request.redirect('/web/login?redirect=/slides/slide/%s' % slide.id)

            if not slide.is_user_allowed_by_batch(user):
                return request.render('irg_batch_slide_restrictions.slide_batch_restriction_error', {
                    'slide': slide,
                })

        # Delega morosidad + prerrequisitos a WebsiteSlidesCustom
        return super(WebsiteSlidesBatchRestrictions, self).slide_view(slide, **kwargs)
