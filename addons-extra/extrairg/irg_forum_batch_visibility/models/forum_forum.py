from odoo import fields, models


class ForumForum(models.Model):
    _inherit = 'forum.forum'

    visibility_batch_ids = fields.Many2many(
        'op.batch',
        'forum_forum_visibility_batch_rel',
        'forum_id',
        'batch_id',
        string='Visibility Batches',
        help='If empty, all users can access this forum. If set, only users in these batches can access it.',
    )
    visibility_course_ids = fields.Many2many(
        'op.course',
        'forum_forum_visibility_course_rel',
        'forum_id',
        'course_id',
        string='Visibility Courses',
        help='Courses linked to this forum (multiple selection).',
    )

    @api.model
    def _visibility_domain_for_user(self, user, course=None):
        """Return the domain that must be applied on forum.forum for *user*.

        The logic mirrors what the portal controller uses.  ``course`` is
        currently ignored (batch-only visibility) but kept in the signature so
        it can be extended later without breaking callers.
        """
        batch_ids = set(user.forum_effective_batch_ids.ids)
        if batch_ids:
            return ['|', ('visibility_batch_ids', '=', False),
                    ('visibility_batch_ids', 'in', list(batch_ids))]
        return [('visibility_batch_ids', '=', False)]

    @api.model
    def forums_visible_for(self, user, course=None):
        """Convenience wrapper: search the forums this user can see.

        Used for automated tests and manual debugging.  Having it on the model
        makes it easier to exercise from shell or server actions.
        """
        domain = self._visibility_domain_for_user(user, course)
        return self.search(domain)
