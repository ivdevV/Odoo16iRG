# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request, route

_logger = logging.getLogger(__name__)


def _lang_code(value):
    """Normaliza el campo lang a un string de código de idioma."""
    if isinstance(value, str):
        return value
    try:
        code = getattr(value, 'code', None)
        if isinstance(code, str):
            return code
    except Exception:
        pass
    return 'en_US'


class IrgHtmlEmbedController(http.Controller):

    @route(
        '/irg/slide/get_embed_content',
        type='json',
        auth='public',
        website=True,
        methods=['POST'],
    )
    def get_embed_content(self, slide_id, **kwargs):
        """
        Devuelve el contenido HTML embebido de un slide (o su html_content normal).

        Respuesta:
            {
                'is_embed': bool,       # True solo cuando hay HTML embebido activo
                'html_content': str,    # El HTML a renderizar
            }
        """
        slide = request.env['slide.slide'].sudo().browse(slide_id)

        if not slide.exists():
            return {'is_embed': False, 'html_content': ''}

        if slide.irg_use_html_embed and slide.irg_html_embed_code and slide.irg_html_embed_code.strip():
            lang = _lang_code(request.env.user.lang)
            html = slide.with_context(lang=lang).irg_html_embed_code or ''
            return {'is_embed': True, 'html_content': html}

        # Artículo normal: devuelve el html_content estándar
        try:
            html_content = request.env['ir.qweb.field.html'].record_to_html(
                slide, 'html_content', {'template_options': {}}
            )
        except Exception:
            html_content = ''
        return {'is_embed': False, 'html_content': html_content}
