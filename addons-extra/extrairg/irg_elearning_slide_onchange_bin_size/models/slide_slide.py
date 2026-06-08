from odoo import models


BINARY_FIELD_ONCHANGE_NAMES = frozenset({
    'binary_content',
    'image_binary_content',
    'document_binary_content',
    'datas',
    'image_1920',
})


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    def _filter_binary_field_onchange(self, field_onchange):
        if not isinstance(field_onchange, dict):
            return field_onchange
        return {
            name: onchange
            for name, onchange in field_onchange.items()
            if name.split('.')[-1] not in BINARY_FIELD_ONCHANGE_NAMES
        }

    def _compute_field_value(self, field):
        if self.env.context.get('irg_in_onchange') and field.name in BINARY_FIELD_ONCHANGE_NAMES:
            for record in self:
                self.env.cache.set(record, field, False)
            return
        super(SlideSlide, self)._compute_field_value(field)

    def onchange(self, values, field_name, field_onchange):
        field_onchange = self._filter_binary_field_onchange(field_onchange)
        if self.env.context.get('bin_size'):
            return super(SlideSlide, self.with_context(irg_in_onchange=True)).onchange(
                values,
                field_name,
                field_onchange,
            )
        return super(SlideSlide, self.with_context(bin_size=True).with_context(irg_in_onchange=True)).onchange(
            values,
            field_name,
            field_onchange,
        )
