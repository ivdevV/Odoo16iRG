from odoo import api, fields, models


class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SlideChannelPartner, self).create(vals_list)
        if self.env.context.get('irg_skip_partner_sync'):
            return records

        to_create_vals = []
        for rec in records:
            channel = rec.channel_id
            if channel.irg_online_channel_id:
                # Check if partner is an Online student for this channel
                if channel._irg_is_partner_online_student_for_channel(rec.partner_id):
                    # Check if already exists in the clone channel
                    exists = self.search([
                        ('channel_id', '=', channel.irg_online_channel_id.id),
                        ('partner_id', '=', rec.partner_id.id)
                    ], limit=1)
                    if not exists:
                        vals = {
                            'channel_id': channel.irg_online_channel_id.id,
                            'partner_id': rec.partner_id.id,
                        }
                        # Sync standard fields if they exist
                        for field in ['completed', 'completion', 'date_from', 'date_to']:
                            if field in self._fields:
                                vals[field] = rec[field]
                        to_create_vals.append(vals)

        if to_create_vals:
            self.with_context(irg_skip_partner_sync=True).create(to_create_vals)

        return records

    def write(self, vals):
        res = super(SlideChannelPartner, self).write(vals)
        if self.env.context.get('irg_skip_partner_sync'):
            return res

        sync_vals = {k: v for k, v in vals.items() if k not in ('channel_id', 'partner_id')}
        if not sync_vals:
            return res

        for rec in self:
            channel = rec.channel_id
            if channel.irg_online_channel_id:
                clone_partner_rec = self.search([
                    ('channel_id', '=', channel.irg_online_channel_id.id),
                    ('partner_id', '=', rec.partner_id.id)
                ], limit=1)
                if clone_partner_rec:
                    clone_partner_rec.with_context(irg_skip_partner_sync=True).write(sync_vals)

        return res

    def unlink(self):
        if not self.env.context.get('irg_skip_partner_sync'):
            for rec in self:
                channel = rec.channel_id
                if channel.irg_online_channel_id:
                    clone_partner_rec = self.search([
                        ('channel_id', '=', channel.irg_online_channel_id.id),
                        ('partner_id', '=', rec.partner_id.id)
                    ])
                    if clone_partner_rec:
                        clone_partner_rec.with_context(irg_skip_partner_sync=True).unlink()
        return super(SlideChannelPartner, self).unlink()
