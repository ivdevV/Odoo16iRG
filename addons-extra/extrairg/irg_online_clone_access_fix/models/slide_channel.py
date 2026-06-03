from odoo import models
from odoo import _


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def _irg_bootstrap_slide_clone_fields(self):
        fields_to_clone = list(super()._irg_bootstrap_slide_clone_fields())
        if 'embed_code' in fields_to_clone:
            fields_to_clone.remove('embed_code')
        for field_name in (
            'datas',
            'document_binary_content',
            'document_binary_content_filename',
            'image_1920',
        ):
            if field_name not in fields_to_clone:
                fields_to_clone.append(field_name)
        return tuple(fields_to_clone)

    def _irg_document_binary_repair_fields(self):
        return (
            'datas',
            'document_binary_content',
            'document_binary_content_filename',
            'image_1920',
        )

    def action_repair_online_clone_documents(self):
        repaired = 0
        inspected = 0
        for channel in self:
            online_channel = channel.irg_online_channel_id
            if not online_channel:
                continue
            cloned_slides = online_channel.slide_ids.filtered('irg_original_slide_id')
            for cloned_slide in cloned_slides:
                source_slide = cloned_slide.irg_original_slide_id
                updates = {}
                inspected += 1
                for field_name in channel._irg_document_binary_repair_fields():
                    if field_name not in source_slide._fields or field_name not in cloned_slide._fields:
                        continue
                    source_value = source_slide[field_name]
                    clone_value = cloned_slide[field_name]
                    if source_value and not clone_value:
                        updates[field_name] = source_value
                if updates:
                    cloned_slide.write(updates)
                    repaired += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reparar documentos Online'),
                'message': _('%d slide(s) reparado(s) de %d revisado(s).') % (repaired, inspected),
                'type': 'success' if repaired else 'info',
                'sticky': False,
            },
        }
