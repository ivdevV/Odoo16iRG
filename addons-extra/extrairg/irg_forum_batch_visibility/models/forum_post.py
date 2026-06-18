from odoo import api, fields, models


class ForumPost(models.Model):
    _inherit = 'forum.post'

    visibility_batch_ids = fields.Many2many(
        'op.batch',
        'forum_post_visibility_batch_rel',
        'post_id',
        'batch_id',
        string='Visibility Batches',
        help='If empty, this post follows the forum batch rules. If set, only users in these batches can read this post.',
    )

    excluded_visibility_batch_ids = fields.Many2many(
        'op.batch',
        'forum_post_excluded_visibility_batch_rel',
        'post_id',
        'batch_id',
        string='Excluded Visibility Batches',
        help='Users in these batches cannot read this post, even if they match the allowed batches.',
    )

    def _is_visible_for_user(self, user, course=None):
        """Return whether *user* can read this post according to forum and post batches."""
        self.ensure_one()
        if not user or user._is_public() or user.has_group('base.group_public'):
            return False
        if user.has_group('base.group_system'):
            return True

        user = user.sudo()
        visible_forums = self.env['forum.forum'].sudo().search(
            self.env['forum.forum']._visibility_domain_for_user(user, course=course)
        )
        if self.forum_id not in visible_forums:
            return False

        user_batch_ids = set(user.forum_effective_batch_ids.ids)
        allowed_batch_ids = set(self.visibility_batch_ids.ids)
        excluded_batch_ids = set(self.excluded_visibility_batch_ids.ids)

        if allowed_batch_ids and not user_batch_ids.intersection(allowed_batch_ids):
            return False
        if excluded_batch_ids and user_batch_ids.intersection(excluded_batch_ids):
            return False
        return True

    def _filter_visible_for_user(self, user, course=None):
        """Filter a post recordset with the same rules used by backend security."""
        return self.filtered(lambda post: post.sudo()._is_visible_for_user(user, course=course))

    def _filter_partners_visible_for_post(self, partners):
        """Keep only partners whose linked user can read this post."""
        self.ensure_one()
        if not partners:
            return partners

        Users = self.env['res.users'].sudo()
        users = Users.search([('partner_id', 'in', partners.ids), ('active', '=', True)])
        visible_partner_ids = set()
        for user in users:
            if self.sudo()._is_visible_for_user(user):
                visible_partner_ids.add(user.partner_id.id)
        return partners.filtered(lambda partner: partner.id in visible_partner_ids)

    @api.model_create_multi
    def create(self, vals_list):
        posts = super().create(vals_list)
        pending_posts = posts.filtered(lambda post: post.state == 'pending')
        if pending_posts:
            pending_posts.sudo().write({
                'state': 'active',
                'active': True,
            })

        # Lógica de notificación inteligente (Biblia iRG)
        for post in posts:
            if not post.forum_id.visibility_batch_ids:
                continue

            # Obtener matrículas confirmadas en los lotes del foro
            enrollments = self.env['op.student.course'].search([
                ('batch_id', 'in', post.forum_id.visibility_batch_ids.ids),
                ('state', '=', 'done')
            ])
            
            student_ids = enrollments.mapped('student_id')
            partners_to_notify = []

            for student in student_ids:
                # Lógica Biblia iRG: ¿Ya cursó/aprobó esto?
                if hasattr(post.forum_id, 'irg_subject_id') and post.forum_id.irg_subject_id:
                    already_passed = self.env['op.student.subject'].search_count([
                        ('student_id', '=', student.id),
                        ('subject_id', '=', post.forum_id.irg_subject_id.id),
                        ('state', '=', 'pass')  # Estado de aprobado
                    ])
                    if already_passed:
                        continue  # Saltamos este alumno, ya lo cursó
                
                partners_to_notify.append(student.partner_id.id)

            # Suscribir silenciosamente a los partners afectados para que Odoo les dispare el email/popup nativo
            if partners_to_notify:
                post.message_subscribe(partner_ids=partners_to_notify)

        return posts
