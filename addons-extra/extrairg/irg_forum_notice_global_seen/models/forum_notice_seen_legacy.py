from odoo import _, api, models
from odoo.exceptions import AccessError


class IrgForumNoticeSeenLegacy(models.Model):
    _inherit = 'irg.forum.notice.seen'

    def _irg_check_mutation_access(self):
        if not self.env.su and not self.env.user.has_group('base.group_system'):
            raise AccessError(
                _('Legacy forum notice seen rows are managed by the system.')
            )

    @api.model_create_multi
    def create(self, vals_list):
        self._irg_check_mutation_access()
        return super().create(vals_list)

    def write(self, vals):
        self._irg_check_mutation_access()
        return super().write(vals)

    def unlink(self):
        self._irg_check_mutation_access()
        return super().unlink()
