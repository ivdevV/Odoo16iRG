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
