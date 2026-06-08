from odoo import models


BINARY_FIELD_ONCHANGE_NAMES = frozenset({
    'binary_content',
    'image_binary_content',
    'document_binary_content',
    'datas',
    'image_1920',
})

SLIDE_RELATION_FIELD_NAMES = frozenset({
    'slide_ids',
    'irg_native_section_ids',
    'irg_online_slide_ids',
    'irg_online_section_ids',
})


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def _is_slide_relation_onchange(self, field_name):
        if not field_name:
            return True
        if isinstance(field_name, str):
            return field_name in SLIDE_RELATION_FIELD_NAMES
        return bool(SLIDE_RELATION_FIELD_NAMES.intersection(field_name))

    def _filter_slide_relation_binary_field_onchange(self, field_onchange):
        if not isinstance(field_onchange, dict):
            return field_onchange
        return {
            name: onchange
            for name, onchange in field_onchange.items()
            if not self._is_slide_relation_binary_field_onchange(name)
        }

    def _is_slide_relation_binary_field_onchange(self, name):
        parts = name.split('.')
        return (
            len(parts) > 1
            and parts[0] in SLIDE_RELATION_FIELD_NAMES
            and parts[-1] in BINARY_FIELD_ONCHANGE_NAMES
        )

    def onchange(self, values, field_name, field_onchange):
        if self._is_slide_relation_onchange(field_name):
            field_onchange = self._filter_slide_relation_binary_field_onchange(
                field_onchange,
            )
        if self.env.context.get('bin_size'):
            return super(SlideChannel, self.with_context(irg_in_onchange=True)).onchange(
                values,
                field_name,
                field_onchange,
            )
        return super(SlideChannel, self.with_context(bin_size=True).with_context(irg_in_onchange=True)).onchange(
            values,
            field_name,
            field_onchange,
        )
