from odoo import models


class ForumForum(models.Model):
    _inherit = 'forum.forum'

    def _irg_web_post_batches(self):
        """Active OpenEduCat batches of the course linked to this forum.

        ``op.batch`` is readable only by OpenEduCat groups. The selector is
        for every internal user, so the catalog is read with sudo. Callers
        still keep only ids from this recordset, which does not widen the
        batches a user can assign.
        """
        self.ensure_one()
        if not self.irg_course_id:
            return self.env['op.batch']
        return self.env['op.batch'].sudo().search([
            ('course_id', '=', self.irg_course_id.id),
            ('active', '=', True),
        ], order='name, id')

    def _irg_sanitize_web_post_batch_ids(self, raw_ids):
        """Keep only active batch ids that belong to this forum's course."""
        self.ensure_one()
        allowed = set(self._irg_web_post_batches().ids)
        cleaned = []
        for raw in raw_ids or []:
            try:
                batch_id = int(raw)
            except (TypeError, ValueError):
                continue
            if batch_id in allowed and batch_id not in cleaned:
                cleaned.append(batch_id)
        return cleaned
