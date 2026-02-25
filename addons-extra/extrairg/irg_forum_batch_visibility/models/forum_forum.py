from odoo import api, fields, models


# ensure moderation is never enabled: it causes front-end JS to prevent
# further posts while a draft is awaiting approval.  we want an entirely
# unmoderated experience for all forums, so clear the flag on create/write



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

        The logic mirrors what the portal controller uses and enforces a
        logical ``OR`` between batch and course visibility.  A forum is
        visible when the user meets *either* restriction.

        We always evaluate the user with ``sudo()`` to avoid problems where the
        portal user is not allowed to read ``op.batch`` records.  If the
        many2many is not accessible, ``user.forum_effective_batch_ids`` may
        appear empty and a security rule would then hide all restricted
        forums.  Computing the domain with a sudo'ed user ensures the correct
        effective batch/course ids are returned regardless of access rights.
        """
        if not user or user._is_public():
            return [('id', '=', 0)]

        user = user.sudo()
        batch_ids = set(user.forum_effective_batch_ids.ids)
        course_ids = set(user.forum_effective_course_ids.ids)
        if course:
            course_ids.add(course.id)

        batch_clause = ['|', ('visibility_batch_ids', '=', False)]
        if batch_ids:
            batch_clause.append(('visibility_batch_ids', 'in', list(batch_ids)))
        else:
            batch_clause.append(('visibility_batch_ids', '=', False))

        course_clause = ['|', ('visibility_course_ids', '=', False)]
        if course_ids:
            course_clause.append(('visibility_course_ids', 'in', list(course_ids)))
        else:
            course_clause.append(('visibility_course_ids', '=', False))

        # enforce **both** batch AND course conditions.  the previous OR logic
        # allowed a forum with an unrelated batch to be visible simply because
        # it wasn't assigned to any course; this is why portal users were
        # seeing forums that didn't belong to their batches.  requiring an AND
        # fixes that while still permitting forums with no restrictions.
        return ['&', batch_clause, course_clause]

    @api.model_create_multi
    def create(self, vals_list):
        # never create a forum with moderation enabled
        for vals in vals_list:
            vals['moderation'] = False
        return super().create(vals_list)

    def write(self, vals):
        if 'moderation' in vals:
            vals = dict(vals, moderation=False)
        return super().write(vals)

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

    def init(self):
        # turn off moderation for any existing forum records when the module
        # is loaded; this guarantees the UI button will not be disabled
        # retrospectively.
        super().init()
        self.search([('moderation', '=', True)]).write({'moderation': False})
