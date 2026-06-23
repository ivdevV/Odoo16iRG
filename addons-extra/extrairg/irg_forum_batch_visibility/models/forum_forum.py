from odoo import api, fields, models
from odoo.osv import expression
from datetime import date


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
        domain="[('course_id', '=', irg_course_id)]",
    )
    visibility_course_ids = fields.Many2many(
        'op.course',
        'forum_forum_visibility_course_rel',
        'forum_id',
        'course_id',
        string='Visibility Courses',
        help='Courses linked to this forum (multiple selection).',
    )

    irg_course_id = fields.Many2one(
        'op.course',
        string='Curso Académico (iRG)',
        help='Selecciona el curso para autocompletar los lotes afectados.',
        options="{'no_create': True, 'no_open': True}",
    )

    irg_subject_id = fields.Many2one(
        'op.subject',
        string='Asignatura (iRG)',
        help='Asignatura específica del foro para filtrar notificaciones.',
        options="{'no_create': True, 'no_open': True}",
    )

    @api.onchange('irg_course_id')
    def _onchange_irg_course_id(self):
        """
        Biblia iRG: Filtrar lotes activos del curso que iniciaron después de
        la era Moodle (01/11/2025) y que ya estén en curso.
        """
        # Limpiar si no hay curso
        if not self.irg_course_id:
            self.visibility_batch_ids = [(5, 0, 0)]
            return {'domain': {'visibility_batch_ids': []}}

        moodle_cutoff = date(2025, 11, 1)
        today = fields.Date.context_today(self)

        # Buscar lotes elegibles
        eligible_batches = self.env['op.batch'].search([
            ('course_id', '=', self.irg_course_id.id),
            ('start_date', '>=', moodle_cutoff),
            ('start_date', '<=', today),
            ('active', '=', True)  # Solo lotes activos
        ])

        # Autoseleccionar (marcar con tilde) usando comando 6
        self.visibility_batch_ids = [(6, 0, eligible_batches.ids)]

        # Restringir el desplegable para que no puedan elegir lotes viejos/inválidos
        return {
            'domain': {
                'visibility_batch_ids': [('id', 'in', eligible_batches.ids)]
            }
        }

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
        if not user or user._is_public() or user.has_group('base.group_public'):
            return [('id', '=', 0)]

        # Only system administrators can bypass forum visibility restrictions.
        if user.has_group('base.group_system'):
            return []

        user = user.sudo()
        batch_ids = set(user.forum_effective_batch_ids.ids)
        course_ids = set(user.forum_effective_course_ids.ids)

        student_link = self.env['op.student'].sudo().search([
            '|',
            ('user_id', '=', user.id),
            ('partner_id', '=', user.partner_id.id),
        ], limit=1)
        is_campus_student = bool(student_link or batch_ids or course_ids)

        if course and course.id:
            # In a course context, only keep that course if the user is
            # effectively enrolled in it. Otherwise, keep course_ids empty so
            # only unrestricted (global) forums can pass the course clause.
            course_ids = {course.id} if course.id in course_ids else set()

        # A forum is visible when BOTH restrictions are satisfied:
        # - Batch: unrestricted OR user belongs to one of the forum batches
        # - Course: unrestricted OR user belongs to one of the forum courses
        #
        # This naturally supports:
        # - global forums (no batch, no course) => visible to everyone
        # - course-only forums => visible to course users
        # - batch-only forums => visible to batch users
        # - course+batch forums => both must match
        if batch_ids:
            batch_clause = ['|', ('visibility_batch_ids', '=', False), ('visibility_batch_ids', 'in', list(batch_ids))] if is_campus_student else [('visibility_batch_ids', 'in', list(batch_ids))]
        else:
            batch_clause = [('visibility_batch_ids', '=', False)] if is_campus_student else [('id', '=', 0)]

        if course_ids:
            course_clause = ['|', ('visibility_course_ids', '=', False), ('visibility_course_ids', 'in', list(course_ids))] if is_campus_student else [('visibility_course_ids', 'in', list(course_ids))]
        else:
            course_clause = [('visibility_course_ids', '=', False)] if is_campus_student else [('id', '=', 0)]

        return expression.AND([batch_clause, course_clause])

    @api.model_create_multi
    def create(self, vals_list):
        # never create a forum with moderation enabled
        if 'moderation' in self._fields:
            for vals in vals_list:
                vals['moderation'] = False
        return super().create(vals_list)

    def write(self, vals):
        if 'moderation' in self._fields and 'moderation' in vals:
            vals = dict(vals, moderation=False)
        return super().write(vals)

    @api.model
    def forums_visible_for(self, user, course=None):
        """Convenience wrapper: search the forums this user can see.

        Used for automated tests and manual debugging.  Having it on the model
        makes it easier to exercise from shell or server actions.

        The search runs without ``sudo()`` and therefore respects record rules.
        The domain itself is still computed from a sudo'ed user to avoid
        false negatives when reading computed enrollment relations.
        """
        domain = self._visibility_domain_for_user(user, course)
        return self.search(domain)

    def init(self):
        # turn off moderation for any existing forum records when the module
        # is loaded; this guarantees the UI button will not be disabled
        # retrospectively.
        super().init()
        # ``moderation`` is not a core field in some installations; guard so
        # the init hook does not crash when the column is absent.
        if 'moderation' in self._fields:
            self.search([('moderation', '=', True)]).write({'moderation': False})
