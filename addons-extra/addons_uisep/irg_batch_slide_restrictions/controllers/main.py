from odoo import http
from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.http import request


class WebsiteSlidesBatchRestrictions(WebsiteSlides):
    @http.route(['/slides/slide/<model("slide.slide"):slide>'], type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        if slide.allowed_batch_ids:
            user = request.env.user
            if user._is_public():
                return request.redirect('/web/login?redirect=/slides/slide/%s' % slide.id)

            if not slide.is_user_allowed_by_batch(user):
                return request.render('irg_batch_slide_restrictions.slide_batch_restriction_error', {
                    'slide': slide,
                })

        return super(WebsiteSlidesBatchRestrictions, self).slide_view(slide, **kwargs)
