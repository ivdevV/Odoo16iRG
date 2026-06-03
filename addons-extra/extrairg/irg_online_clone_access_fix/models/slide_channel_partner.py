from odoo import api, models


class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    def _irg_online_clone_sync_fields(self):
        return (
            'active', 'completed', 'completion', 'date_from', 'date_to',
            'course_id', 'register_id', 'admission_id', 'batch_id', 'op_subject_id',
        )

    def _irg_prepare_online_clone_sync_values(self):
        self.ensure_one()
        vals = {}
        for field_name in self._irg_online_clone_sync_fields():
            if field_name not in self._fields:
                continue
            field = self._fields[field_name]
            value = self[field_name]
            if field.type == 'many2one':
                vals[field_name] = value.id if value else False
            else:
                vals[field_name] = value
        return vals

    def _irg_sync_academic_fields_to_online_clone(self):
        if self.env.context.get('irg_skip_partner_sync'):
            return
        Partner = self.sudo()
        for rec in Partner:
            channel = rec.channel_id
            online_channel = channel.irg_online_channel_id if channel and 'irg_online_channel_id' in channel._fields else False
            if not online_channel:
                continue
            clone_partner = Partner.search([
                ('channel_id', '=', online_channel.id),
                ('partner_id', '=', rec.partner_id.id),
            ], limit=1)
            if clone_partner:
                clone_partner.with_context(irg_skip_partner_sync=True).write(
                    rec._irg_prepare_online_clone_sync_values()
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_sync_academic_fields_to_online_clone()
        return records

    def write(self, vals):
        res = super().write(vals)
        if set(vals).intersection(self._irg_online_clone_sync_fields()):
            self._irg_sync_academic_fields_to_online_clone()
        return res
