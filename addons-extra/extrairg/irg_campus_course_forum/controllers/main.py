from odoo import http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.isep_website_custom_inh.controllers.main import DashboardPortalInh


class DashboardPortalCampusForum(DashboardPortalInh):

    def _get_user_batch_ids_for_course(self, user, course):
        batch_ids = set(user.op_batch_ids.ids)

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
        return request.env['forum.forum']._visibility_domain_for_user(request.env.user, course=course)

    @http.route(['/campus/course/<int:course_id>'], type='http', auth="user", website=True)
    def view_user_profile_course(self, course_id, **post):
        response = super().view_user_profile_course(course_id, **post)

        course = request.env['op.course'].sudo().browse(course_id)
        forum_ids = request.env['forum.forum']
        post_ids = request.env['forum.post']
        posts_by_forum_id = {}
        user = request.env.user

        # ``course`` is obtained in sudo mode, so exists() should normally
        # be True.  nevertheless we still guard in case the course id is
        # bogus.  we also initialise debug variables here to avoid later
        # None-values confusing the template.
        debug_domain = None
        debug_forums = None
        debug_course = None

        if course.exists():
            user_batch_ids = self._get_user_batch_ids_for_course(user, course)
            forum_domain = self._forum_visibility_domain_for_user(course, user_batch_ids)

            debug_domain = forum_domain
            debug_course = course.id

            # debug log – helps troubleshooting missing forums for specific users
            _logger = request.env['ir.logging'].sudo()
            try:
                _logger.create({
                    'name': 'campus_forum_debug',
                    'type': 'server',
                    'level': 'info',
                    'dbname': request.env.cr.dbname,
                    'message': f"forum_domain={forum_domain} course={course.id}",
                    'path': 'irg_campus_course_forum.controllers.main',
                    'func': '_forum_debug',
                    'line': '0',
                })
            except Exception:
                pass

            forum_ids = request.env['forum.forum'].search(forum_domain, order='name asc')

            # debug : record what forums were found after the sudo search
            try:
                _logger.create({
                    'name': 'campus_forum_debug',
                    'type': 'server',
                    'level': 'info',
                    'dbname': request.env.cr.dbname,
                    'message': (
                        f"forums_found={[f.name for f in forum_ids]} "
                        f"forum_domain={forum_domain} "
                        f"course={course.id}"),
                    'path': 'irg_campus_course_forum.controllers.main',
                    'func': '_forum_debug',
                    'line': '0',
                })
            except Exception:
                pass

            forum_ids = forum_ids.sorted(key=lambda forum: forum.name or '')

            if forum_ids:
                post_domain = [
                    ('forum_id', 'in', forum_ids.ids),
                    ('parent_id', '=', False),
                ]
                post_ids = request.env['forum.post'].search(post_domain, order='create_date desc')
                posts_by_forum_id = {
                    forum.id: post_ids.filtered(lambda forum_post: forum_post.forum_id == forum)
                    for forum in forum_ids
                }

        if hasattr(response, 'qcontext'):
            # expose debugging info so a portal user can inspect what domain
            # was generated; this avoids needing to check server logs.
            response.qcontext.update({
                'course_forum': forum_ids[:1],
                'course_forum_ids': forum_ids,
                'course_forum_post_ids': post_ids,
                'course_forum_posts_map': posts_by_forum_id,
                'debug_forum_domain': debug_domain,
                'debug_course_id': debug_course,
                'debug_forums_found': debug_forums or [(f.id, f.name) for f in forum_ids],
            })

        return response
