from odoo import models


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    def onchange(self, values, field_name, field_onchange):
        if self.env.context.get('bin_size'):
            return super().onchange(values, field_name, field_onchange)
        return super(SlideSlide, self.with_context(bin_size=True)).onchange(
            values,
            field_name,
            field_onchange,
        )
