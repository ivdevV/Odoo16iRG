import logging

from psycopg2 import IntegrityError

from odoo import api, fields, models


_logger = logging.getLogger(__name__)
_UNIQUE_INDEX = 'irg_scp_active_partner_channel_batch_uniq'


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
                    exists = self.with_context(active_test=False).search([
                        ('channel_id', '=', channel.irg_online_channel_id.id),
                        ('partner_id', '=', rec.partner_id.id),
                        ('batch_id', '=', rec.batch_id.id if rec.batch_id else False),
                    ], order='active DESC, create_date ASC', limit=1)
                    if not exists:
                        vals = {
                            'channel_id': channel.irg_online_channel_id.id,
                            'partner_id': rec.partner_id.id,
                            'batch_id': rec.batch_id.id if rec.batch_id else False,
                        }
                        # Sync standard fields if they exist
                        for field in ['completed', 'completion', 'date_from', 'date_to']:
                            if field in self._fields:
                                vals[field] = rec[field]
                        to_create_vals.append(vals)

        for values in to_create_vals:
            try:
                with self.env.cr.savepoint():
                    self.with_context(irg_skip_partner_sync=True).create(values)
            except IntegrityError as exc:
                if exc.diag.constraint_name != _UNIQUE_INDEX:
                    raise
                _logger.info(
                    'Concurrent initial online clone membership already exists for partner %s',
                    values['partner_id'],
                )

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
                clone_partner_rec = self.with_context(active_test=False).search([
                    ('channel_id', '=', channel.irg_online_channel_id.id),
                    ('partner_id', '=', rec.partner_id.id),
                    ('batch_id', '=', rec.batch_id.id if rec.batch_id else False),
                ], order='active DESC, create_date ASC', limit=1)
                if clone_partner_rec:
                    clone_partner_rec.with_context(irg_skip_partner_sync=True).write(sync_vals)

        return res

    def unlink(self):
        if not self.env.context.get('irg_skip_partner_sync'):
            for rec in self:
                channel = rec.channel_id
                if channel.irg_online_channel_id:
                    clone_partner_rec = self.with_context(active_test=False).search([
                        ('channel_id', '=', channel.irg_online_channel_id.id),
                        ('partner_id', '=', rec.partner_id.id),
                        ('batch_id', '=', rec.batch_id.id if rec.batch_id else False),
                    ])
                    if clone_partner_rec:
                        clone_partner_rec.with_context(irg_skip_partner_sync=True).unlink()
        return super(SlideChannelPartner, self).unlink()
