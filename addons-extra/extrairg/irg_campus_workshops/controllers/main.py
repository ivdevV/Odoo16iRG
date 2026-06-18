# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from odoo.addons.website_slides.controllers.main import WebsiteSlides

_logger = logging.getLogger(__name__)


class WebsiteSlidesWorkshops(WebsiteSlides):

    @http.route([
        '/slides/<model("slide.channel"):channel>',
        '/slides/<model("slide.channel"):channel>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=WebsiteSlides.sitemap_slide)
    def channel(self, channel, category=None, tag=None, page=1, slide_category=None,
                uncategorized=False, sorting=None, search=None, **kw):
        """Sobrescribe la ruta de acceso al canal de diapositivas para auto-inscribir a los usuarios
        autenticados si acceden al canal de iRG Empower.
        """
        # Si el usuario está autenticado y no es el usuario público
        if request.env.user and not request.env.user._is_public():
            # Si el canal es el de iRG Empower (ID 261 o contiene 'empower' en el nombre)
            if channel.id == 261 or 'empower' in (channel.name or '').lower():
                partner = request.env.user.partner_id
                # Comprobar si ya está inscrito
                membership = request.env['slide.channel.partner'].sudo().search([
                    ('partner_id', '=', partner.id),
                    ('channel_id', '=', channel.id)
                ], limit=1)
                
                if not membership:
                    _logger.info("[WORKSHOPS] Auto-enrolling user %s (Partner: %s) in workshop channel: %s (ID: %s)", 
                                 request.env.user.name, partner.id, channel.name, channel.id)
                    create_vals = {
                        'partner_id': partner.id,
                        'channel_id': channel.id,
                    }
                    # Comprobar defensivamente si el campo 'auto_added' está disponible en el modelo
                    if 'auto_added' in request.env['slide.channel.partner']._fields:
                        create_vals['auto_added'] = True
                        
                    request.env['slide.channel.partner'].sudo().create(create_vals)

        return super(WebsiteSlidesWorkshops, self).channel(
            channel,
            category=category,
            tag=tag,
            page=page,
            slide_category=slide_category,
            uncategorized=uncategorized,
            sorting=sorting,
            search=search,
            **kw
        )
