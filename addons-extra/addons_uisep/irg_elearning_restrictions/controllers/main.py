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

        if slide.restriction_slide_ids:
            user = request.env.user
            # Si es public user, pedir login
            if user._is_public():
                return request.redirect('/web/login?redirect=/slides/slide/%s' % slide.id)

            # Comprobar que TODOS los requisitos están completados
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
        
        return super(WebsiteSlidesCustom, self).slide_view(slide, **kwargs)
