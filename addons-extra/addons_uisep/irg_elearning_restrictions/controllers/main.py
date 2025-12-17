from odoo import http, _
from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.http import request

class WebsiteSlidesCustom(WebsiteSlides):
    @http.route(['/slides/slide/<model("slide.slide"):slide>'], type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        if slide.restriction_slide_id:
            user = request.env.user
            # Si es public user, probablemente queramos bloquear o pedir login
            if user._is_public():
                 return request.redirect('/web/login?redirect=/slides/slide/%s' % slide.id)

            # Check if prerequisite is completed
            domain = [
                ('slide_id', '=', slide.restriction_slide_id.id),
                ('partner_id', '=', user.partner_id.id),
                ('completed', '=', True)
            ]
            has_completed = request.env['slide.slide.partner'].sudo().search_count(domain)
            
            if not has_completed:
                # Opción A: Redirigir al requisito
                return request.render('irg_elearning_restrictions.slide_restriction_error', {
                    'slide': slide,
                    'prerequisite': slide.restriction_slide_id,
                })
        
        return super(WebsiteSlidesCustom, self).slide_view(slide, **kwargs)
