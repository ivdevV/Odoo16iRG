from odoo import http
from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.http import request
from datetime import date

class WebsiteSlidesScheduled(WebsiteSlides):

    @http.route(['/slides/slide/<model("slide.slide"):slide>'], type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        # Verificar si hay fecha programada y si aún no ha llegado
        if slide.scheduled_date:
            today = date.today()
            if today < slide.scheduled_date:
                return request.render('irg_elearning_scheduled.slide_scheduled_error', {
                    'slide': slide,
                    'scheduled_date': slide.scheduled_date,
                })
        
        return super(WebsiteSlidesScheduled, self).slide_view(slide, **kwargs)
