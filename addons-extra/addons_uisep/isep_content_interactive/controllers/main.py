from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.http import request, route
from odoo import http
import logging
_logger = logging.getLogger(__name__)


def _normalize_lang(value):
    if isinstance(value, str):
        return value
    try:
        code = getattr(value, 'code', None)
        if isinstance(code, str):
            return code
    except Exception:
        pass
    return None


class WebsiteSlidesInh(WebsiteSlides):

    @route('/slides/slide/get_html_content', type='json', auth='public', website=True)
    def get_html_content(self, slide_id):
        slide = request.env['slide.slide'].sudo().browse(slide_id)
        if not slide.exists():
            return {'html_content': ''}

        lang = _normalize_lang(request.env.user.lang) or 'en_US'

        if slide.use_html_embed and slide.html_embed_code:
            html = slide.with_context(lang=lang).html_embed_code or ''
            return {
                'html_content': html,
                'is_embed': True,
            }

        html_content = request.env['ir.qweb.field.html'].record_to_html(
            slide, 'html_content', {'template_options': {}}
        )
        return {'html_content': html_content}