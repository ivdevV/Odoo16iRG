from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class Slide(models.Model):
    _inherit = 'slide.slide'

    restriction_slide_id = fields.Many2one(
        'slide.slide',
        string='Diapositiva Requisito (Test)',
        help='La diapositiva que debe completarse antes de acceder a esta.'
    )

    def _check_prerequisite(self):
        """ Check if the user has completed the prerequisite slide. """
        for slide in self:
            if slide.restriction_slide_id and not self.env.is_superuser():
                user = self.env.user
                # Skip check for public user if we want them to see the slide exists (but maybe not content)
                # But usually we want to restrict content.
                
                # Check if prerequisite is completed
                domain = [
                    ('slide_id', '=', slide.restriction_slide_id.id),
                    ('partner_id', '=', user.partner_id.id),
                    ('completed', '=', True)
                ]
                has_completed = self.env['slide.slide.partner'].sudo().search_count(domain)
                
                if not has_completed:
                    raise AccessError(_('No puedes acceder a este contenido hasta completar el requisito: %s') % slide.restriction_slide_id.name)

    def read(self, fields=None, load='_classic_read'):
        # Hook into read to enforce restriction when accessing content fields
        # We avoid checking on basic fields to allow list views to render
        content_fields = ['embed_code', 'video_url', 'document_google_url', 'url', 'datas', 'db_datas']
        if fields and any(f in fields for f in content_fields):
            self._check_prerequisite()
        return super(Slide, self).read(fields=fields, load=load)


