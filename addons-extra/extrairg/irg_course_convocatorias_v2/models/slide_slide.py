from odoo import api, fields, models


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_content_modality = fields.Selection(
        selection=[('homeclass', 'HomeClass'), ('online', 'Online')],
        string='Modalidad iRG',
        index=True,
        help='Permite separar el contenido del curso entre HomeClass y Online dentro del mismo canal.',
    )
    irg_display_category = fields.Char(
        string='Categoría iRG',
        compute='_compute_irg_display_category',
    )

    @api.depends('is_category', 'slide_category')
    def _compute_irg_display_category(self):
        slide_category_field = self._fields.get('slide_category')
        category_labels = (
            dict(slide_category_field._description_selection(self.env))
            if slide_category_field else {}
        )
        for slide in self:
            if slide.is_category:
                slide.irg_display_category = 'Sección'
            else:
                slide.irg_display_category = category_labels.get(
                    slide.slide_category,
                    slide.slide_category or '',
                )
