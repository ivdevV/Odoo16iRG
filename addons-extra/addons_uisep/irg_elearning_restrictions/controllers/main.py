from odoo import http, _
from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.http import request

class WebsiteSlidesCustom(WebsiteSlides):
    def _is_debtor_blocked(self):
        user = request.env.user
        if not user or user._is_public():
            return False

        category_names = [name.lower() for name in user.partner_id.category_id.mapped('name') if name]
        return any(('morosidad' in name) or ('burofax' in name) for name in category_names)

    @http.route(['/slides/slide/<model("slide.slide"):slide>'], type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        if self._is_debtor_blocked():
            return request.render('irg_elearning_restrictions.slide_access_blocked', {
                'slide': slide,
            })

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
