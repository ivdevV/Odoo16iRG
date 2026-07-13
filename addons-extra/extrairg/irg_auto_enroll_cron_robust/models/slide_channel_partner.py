from odoo import api, models, tools, _
from odoo.exceptions import ValidationError


_UNIQUE_INDEX = 'irg_scp_active_partner_channel_batch_uniq'


class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    @api.constrains('channel_id', 'partner_id', 'batch_id', 'active')
    def _check_unique_channel_partner_active(self):
        """Align the inherited Python check with the approved per-batch key."""
        for record in self.filtered('active'):
            duplicate = self.search_count([
                ('channel_id', '=', record.channel_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('batch_id', '=', record.batch_id.id if record.batch_id else False),
                ('active', '=', True),
                ('id', '!=', record.id),
            ])
            if duplicate:
                raise ValidationError(_(
                    'An active membership already exists for this partner, channel and batch.'
                ))

    def _irg_assert_no_active_membership_duplicates(self):
        self.env.cr.execute("""
            SELECT partner_id, channel_id, batch_id
              FROM slide_channel_partner
             WHERE active IS TRUE AND batch_id IS NOT NULL
          GROUP BY partner_id, channel_id, batch_id
            HAVING count(*) > 1
             LIMIT 1
        """)
        duplicate = self.env.cr.fetchone()
        if duplicate:
            raise ValidationError(_(
                'Cannot install robust auto-enroll: duplicate active membership '
                'for partner %(partner)s, channel %(channel)s and batch %(batch)s.',
                partner=duplicate[0],
                channel=duplicate[1],
                batch=duplicate[2],
            ))

    def _auto_init(self):
        result = super()._auto_init()
        self._irg_assert_no_active_membership_duplicates()
        if not tools.index_exists(self.env.cr, _UNIQUE_INDEX):
            self.env.cr.execute("""
                CREATE UNIQUE INDEX irg_scp_active_partner_channel_batch_uniq
                    ON slide_channel_partner (partner_id, channel_id, batch_id)
                 WHERE active IS TRUE AND batch_id IS NOT NULL
            """)
        return result
