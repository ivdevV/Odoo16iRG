from odoo import http
from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.http import request
from datetime import date


class WebsiteSlidesBatchRestrictions(WebsiteSlides):
    @http.route(['/slides/slide/<model("slide.slide"):slide>'], type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        if slide.scheduled_date:
            today = date.today()
            if today < slide.scheduled_date:
                return request.render('irg_elearning_scheduled.slide_scheduled_error', {
                    'slide': slide,
                    'scheduled_date': slide.scheduled_date,
                })

        if slide.restriction_slide_id:
            user = request.env.user
            if user._is_public():
                return request.redirect('/web/login?redirect=/slides/slide/%s' % slide.id)

            domain = [
                ('slide_id', '=', slide.restriction_slide_id.id),
                ('partner_id', '=', user.partner_id.id),
                ('completed', '=', True)
            ]
            has_completed = request.env['slide.slide.partner'].sudo().search_count(domain)
            if not has_completed:
                return request.render('irg_elearning_restrictions.slide_restriction_error', {
                    'slide': slide,
                    'prerequisite': slide.restriction_slide_id,
                })

        if slide.sudo().allowed_batch_ids:
            user = request.env.user
            if user._is_public():
                return request.redirect('/web/login?redirect=/slides/slide/%s' % slide.id)

            if not slide.is_user_allowed_by_batch(user):
                return request.render('irg_batch_slide_restrictions.slide_batch_restriction_error', {
                    'slide': slide,
                })

        return super(WebsiteSlidesBatchRestrictions, self).slide_view(slide, **kwargs)
