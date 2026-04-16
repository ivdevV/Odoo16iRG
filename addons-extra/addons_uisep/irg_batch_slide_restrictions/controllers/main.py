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

        if slide.restriction_slide_ids:
            user = request.env.user
            if user._is_public():
                return request.redirect('/web/login?redirect=/slides/slide/%s' % slide.id)

            completed_slide_ids = set(
                request.env['slide.slide.partner'].sudo().search([
                    ('partner_id', '=', user.partner_id.id),
                    ('completed', '=', True),
                ]).mapped('slide_id').ids
            )
            missing = slide.restriction_slide_ids.filtered(
                lambda s: s.id not in completed_slide_ids
            )
            if missing:
                return request.render('irg_elearning_restrictions.slide_restriction_error', {
                    'slide': slide,
                    'prerequisites': missing,
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
