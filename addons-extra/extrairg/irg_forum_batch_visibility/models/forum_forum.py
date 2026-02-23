from odoo import api, fields, models


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

        We always evaluate the user with ``sudo()`` to avoid problems where the
        portal user is not allowed to read ``op.batch`` records.  If the
        many2many is not accessible, ``user.forum_effective_batch_ids`` may
        appear empty and a security rule would then hide all restricted
        forums.  Computing the domain with a sudo'ed user ensures the correct
        batch ids are returned regardless of access rights.  The caller can
        still search with or without ``sudo()`` depending on context; tests
        and the website controller now use ``sudo()`` explicitly too.
        """
        # ``user`` may be a browse record from an unprivileged environment;
        # make sure we use sudo() so that the computed relation is visible.
        user = user.sudo()
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

        The search is performed with ``sudo()`` so that portal users aren't
        accidentally blocked by the security rule that references
        ``user.forum_effective_batch_ids`` (which may not be readable without
        additional batch permissions).  The caller can still pass an ordinary
        ``user`` record; the method handles the privilege escalation
        internally.  Tests that previously inspected the results without
        ``sudo()`` continue to work.
        """
        domain = self._visibility_domain_for_user(user, course)
        return self.sudo().search(domain)
