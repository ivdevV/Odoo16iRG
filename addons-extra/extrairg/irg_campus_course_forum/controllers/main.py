from odoo import http
from odoo.http import request

from odoo.addons.isep_website_custom_inh.controllers.main import DashboardPortalInh


class DashboardPortalCampusForum(DashboardPortalInh):

    def _get_user_batch_ids_for_course(self, user, course):
        batch_ids = set(user.forum_effective_batch_ids.ids)
        batch_ids.update(user.op_batch_ids.ids)

        student_ids = request.env['op.student'].sudo().search([
            '|',
            ('user_id', '=', user.id),
            ('partner_id', '=', user.partner_id.id),
        ])

        admission_batch_ids = request.env['op.admission'].sudo().search([
            ('course_id', '=', course.id),
            ('batch_id', '!=', False),
            '|',
            ('partner_id', '=', user.partner_id.id),
            ('student_id', 'in', student_ids.ids),
        ]).mapped('batch_id').ids
        batch_ids.update(admission_batch_ids)

        student_course_batch_ids = request.env['op.student.course'].sudo().search([
            ('course_id', '=', course.id),
            ('batch_id', '!=', False),
            ('state', '!=', 'finished'),
            ('student_id', 'in', student_ids.ids),
        ]).mapped('batch_id').ids
        batch_ids.update(student_course_batch_ids)

        return batch_ids

    def _forum_visibility_domain_for_user(self, course, user_batch_ids):
        # Only batches determine visibility; course restrictions are dropped because
        # students cannot access masters they are not enrolled in, so checking
        # course is redundant and may hide forums when a batch already grants access.
        if user_batch_ids:
            return ['|', ('visibility_batch_ids', '=', False), ('visibility_batch_ids', 'in', list(user_batch_ids))]
        return [('visibility_batch_ids', '=', False)]

    @http.route(['/campus/course/<int:course_id>'], type='http', auth="user", website=True)
    def view_user_profile_course(self, course_id, **post):
        response = super().view_user_profile_course(course_id, **post)

        course = request.env['op.course'].browse(course_id)
        forum_ids = request.env['forum.forum']
        post_ids = request.env['forum.post']
        posts_by_forum_id = {}
        user = request.env.user

        if course.exists():
            user_batch_ids = self._get_user_batch_ids_for_course(user, course)

            forum_domain = self._forum_visibility_domain_for_user(course, user_batch_ids)
            # debug log – helps troubleshooting missing forums for specific users
            _logger = request.env['ir.logging'].sudo()
            try:
                _logger.create({
                    'name': 'campus_forum_debug',
                    'type': 'server',
                    'level': 'debug',
                    'dbname': request.env.cr.dbname,
                    'message': f"forum_domain={forum_domain} user_batch_ids={list(user_batch_ids)} course={course.id}",
                    'path': 'irg_campus_course_forum.controllers.main',
                    'func': '_forum_debug',
                    'line': '0',
                })
            except Exception:
                pass

            # perform the search with sudo so that the portal record rule
            # (which also references ``user.forum_effective_batch_ids``) cannot
            # further restrict the result.  if we used the plain env the
            # rule might evaluate the batch list as empty and return only
            # forums without any restriction, which is exactly the behaviour
            # we have seen in production.
            forum_ids = request.env['forum.forum'].sudo().search(forum_domain, order='name asc')

            if not forum_ids and user_batch_ids:
                # fallback: if the previous search returned nothing, try a
                # simpler query so we can log what batches we think we have.
                forum_ids = request.env['forum.forum'].sudo().search([
                    ('visibility_batch_ids', 'in', list(user_batch_ids)),
                ], order='name asc')

            # debug : record what forums we managed to find after sudo
            try:
                _logger.create({
                    'name': 'campus_forum_debug',
                    'type': 'server',
                    'level': 'debug',
                    'dbname': request.env.cr.dbname,
                    'message': (
                        f"forums_found={[f.name for f in forum_ids]} "
                        f"forum_domain={forum_domain} "
                        f"user_batch_ids={list(user_batch_ids)} "
                        f"course={course.id}"),
                    'path': 'irg_campus_course_forum.controllers.main',
                    'func': '_forum_debug',
                    'line': '0',
                })
            except Exception:
                pass

            if course.forum_id and course.forum_id in request.env['forum.forum'].search(forum_domain + [('id', '=', course.forum_id.id)]):
                forum_ids |= course.forum_id

            forum_ids = forum_ids.sorted(key=lambda forum: forum.name or '')

            if forum_ids:
                post_domain = [
                    ('forum_id', 'in', forum_ids.ids),
                    ('parent_id', '=', False),
                ]
                if user_batch_ids:
                    post_domain += ['|', ('visibility_batch_ids', '=', False), ('visibility_batch_ids', 'in', list(user_batch_ids))]
                else:
                    post_domain += [('visibility_batch_ids', '=', False)]

                post_ids = request.env['forum.post'].search(post_domain, order='create_date desc')
                posts_by_forum_id = {
                    forum.id: post_ids.filtered(lambda forum_post: forum_post.forum_id == forum)
                    for forum in forum_ids
                }

        if hasattr(response, 'qcontext'):
            response.qcontext.update({
                'course_forum': forum_ids[:1],
                'course_forum_ids': forum_ids,
                'course_forum_post_ids': post_ids,
                'course_forum_posts_map': posts_by_forum_id,
            })

        return response
