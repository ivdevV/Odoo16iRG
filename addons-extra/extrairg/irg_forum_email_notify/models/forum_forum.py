import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ForumForum(models.Model):
    _inherit = 'forum.forum'

    email_notify_enabled = fields.Boolean(
        string='Notificaciones por email',
        default=True,
        help=(
            'Si está activado, se envía un correo electrónico a los '
            'participantes elegibles cada vez que se publica un nuevo '
            'mensaje en este foro.'
        ),
    )

    # ------------------------------------------------------------------
    # Recipient computation
    # ------------------------------------------------------------------

    def _get_notification_recipients(self, exclude_partner=None):
        """Return *res.partner* records that should receive an email
        notification for a new post in this forum.

        The logic mirrors the forum visibility rules:
        * If the forum has ``visibility_batch_ids`` → users enrolled in
          those batches (via ``op.student.course`` or ``op.admission``),
          plus users with a direct ``op_batch_ids`` assignment.
        * If the forum also has ``visibility_course_ids`` → intersect
          with users enrolled in those courses.
        * If the forum has ``visibility_course_ids`` only (no batches) →
          all users enrolled in those courses.
        * If neither is set → all active students with a portal user.

        Partners without an email address, the post author (via
        *exclude_partner*), and users who have opted out of this forum
        are excluded from the result.
        """
        self.ensure_one()
        forum = self.sudo()

        Student = self.env['op.student'].sudo()
        SC = self.env['op.student.course'].sudo()
        Adm = self.env['op.admission'].sudo()
        Users = self.env['res.users'].sudo()

        batch_ids = forum.visibility_batch_ids.ids
        course_ids = forum.visibility_course_ids.ids

        partners = self.env['res.partner'].sudo()

        if not batch_ids and not course_ids:
            # No restrictions → all students that have a portal user
            students = Student.search([('user_id', '!=', False)])
            partners = students.mapped('partner_id')
        else:
            batch_partners = None
            course_partners = None

            if batch_ids:
                batch_partners = self._partners_for_batches(
                    batch_ids, Student, SC, Adm, Users,
                )

            if course_ids:
                course_partners = self._partners_for_courses(
                    course_ids, Student, SC, Adm, Users,
                )

            # Combine: AND when both are set, single set otherwise
            if batch_partners is not None and course_partners is not None:
                partners = batch_partners & course_partners
            elif batch_partners is not None:
                partners = batch_partners
            else:
                partners = course_partners or partners

        # Must have an email address
        partners = partners.filtered('email')

        if not partners:
            forum_batch_ids = set(batch_ids)
            forum_course_ids = set(course_ids)
            all_users = Users.search([
                ('active', '=', True),
                ('partner_id', '!=', False),
            ])
            fallback_partners = self.env['res.partner'].sudo()
            for user_rec in all_users:
                user_batch_ids = set(user_rec.forum_effective_batch_ids.ids) | set(user_rec.op_batch_ids.ids)
                user_course_ids = set(user_rec.forum_effective_course_ids.ids)
                batch_ok = not forum_batch_ids or bool(user_batch_ids & forum_batch_ids)
                course_ok = not forum_course_ids or bool(user_course_ids & forum_course_ids)
                if batch_ok and course_ok:
                    fallback_partners |= user_rec.partner_id
            partners = fallback_partners.filtered('email')

        # Exclude post author
        if exclude_partner:
            partners -= exclude_partner

        # Exclude users who opted out of this forum
        opted_out_users = Users.search([
            ('forum_email_optout_ids', 'in', [self.id]),
        ])
        if opted_out_users:
            partners -= opted_out_users.mapped('partner_id')

        return partners

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _partners_for_batches(batch_ids, Student, SC, Adm, Users):
        """Collect partners linked to the given batch IDs."""
        # Students enrolled via op.student.course
        sc_students = SC.search([
            ('batch_id', 'in', batch_ids),
            ('state', '!=', 'finished'),
        ]).mapped('student_id')

        # Students found via op.admission
        adm_recs = Adm.search([('batch_id', 'in', batch_ids)])
        adm_students = Student.browse()
        if adm_recs:
            adm_partner_ids = adm_recs.mapped('partner_id').ids
            adm_student_ids = adm_recs.filtered('student_id').mapped('student_id').ids
            domain = []
            if adm_partner_ids:
                domain.append(('partner_id', 'in', adm_partner_ids))
            if adm_student_ids:
                if domain:
                    domain = ['|'] + domain + [('id', 'in', adm_student_ids)]
                else:
                    domain = [('id', 'in', adm_student_ids)]
            if domain:
                adm_students = Student.search(domain)

        # Users with a direct op_batch_ids assignment
        direct_users = Users.search([('op_batch_ids', 'in', batch_ids)])

        return (
            (sc_students | adm_students).mapped('partner_id')
            | direct_users.mapped('partner_id')
        )

    @staticmethod
    def _partners_for_courses(course_ids, Student, SC, Adm, Users):
        """Collect partners linked to the given course IDs."""
        sc_students = SC.search([
            ('course_id', 'in', course_ids),
            ('state', '!=', 'finished'),
        ]).mapped('student_id')

        adm_recs = Adm.search([('course_id', 'in', course_ids)])
        adm_students = Student.browse()
        if adm_recs:
            adm_partner_ids = adm_recs.mapped('partner_id').ids
            adm_student_ids = adm_recs.filtered('student_id').mapped('student_id').ids
            domain = []
            if adm_partner_ids:
                domain.append(('partner_id', 'in', adm_partner_ids))
            if adm_student_ids:
                if domain:
                    domain = ['|'] + domain + [('id', 'in', adm_student_ids)]
                else:
                    domain = [('id', 'in', adm_student_ids)]
            if domain:
                adm_students = Student.search(domain)

        direct_users = Users.browse()
        if 'op_batch_ids' in Users._fields and 'course_id' in Users.env['op.batch']._fields:
            direct_users = Users.search([('op_batch_ids.course_id', 'in', course_ids)])

        return (sc_students | adm_students).mapped('partner_id') | direct_users.mapped('partner_id')
