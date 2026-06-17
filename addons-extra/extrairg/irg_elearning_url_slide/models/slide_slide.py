# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    nbr_url = fields.Integer(string='URL Slides', store=True)


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    nbr_url = fields.Integer(string='URL', store=True)
    slide_category = fields.Selection(
        selection_add=[('url', 'URL')],
        ondelete={'url': 'set default'},
    )
    slide_type = fields.Selection(
        selection_add=[('url', 'URL')],
        ondelete={'url': 'set null'},
        compute='_compute_slide_type',
        store=True,
    )
    irg_url = fields.Char(string='URL')
    irg_url_button_label = fields.Char(
        string='Texto del boton',
        default='Ir al contenido',
        translate=True,
    )

    @api.depends('slide_category', 'source_type', 'video_source_type')
    def _compute_slide_type(self):
        res = super()._compute_slide_type()
        for slide in self:
            if slide.slide_category == 'url':
                slide.slide_type = 'url'
        return res

    @api.depends('slide_category', 'irg_url', 'irg_url_button_label')
    def _compute_embed_code(self):
        res = super()._compute_embed_code()
        for slide in self:
            if slide.slide_category == 'url' and slide.irg_url:
                label = slide.irg_url_button_label or _('Ir al contenido')
                slide.embed_code = Markup(
                    '<div class="o_irg_url_slide card border-0 shadow-sm">'
                    '<div class="card-body text-center p-4">'
                    '<i class="fa fa-link fa-2x text-primary mb-3" aria-hidden="true"></i>'
                    '<h4 class="mb-3">%s</h4>'
                    '<a class="btn btn-primary" href="%s">%s</a>'
                    '</div>'
                    '</div>'
                ) % (slide.name or _('Contenido URL'), slide.irg_url, label)
                slide.embed_code_external = slide.embed_code
        return res

    @api.constrains('slide_category', 'irg_url')
    def _check_irg_url(self):
        for slide in self:
            if slide.slide_category != 'url':
                continue
            if not slide.irg_url:
                raise ValidationError(_('Debe indicar una URL para el tipo de contenido URL.'))
            parsed_url = urlparse(slide.irg_url)
            if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
                raise ValidationError(_('La URL debe empezar por http:// o https://.'))
