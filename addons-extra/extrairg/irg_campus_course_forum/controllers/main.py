from odoo import http
from odoo.http import request

from odoo.addons.isep_website_custom.controllers.main import DashboardPortal


class DashboardPortalCampusForum(DashboardPortal):

    @http.route(['/campus/course/<int:course_id>'], type='http', auth="user", website=True)
    def view_user_profile_course(self, course_id, **post):
        response = super().view_user_profile_course(course_id, **post)

        course = request.env['op.course'].browse(course_id)
        forum_ids = request.env['forum.forum']
        post_ids = request.env['forum.post']
        posts_by_forum_id = {}

        if course.exists():
            forum_ids = request.env['forum.forum'].search([
                ('visibility_course_ids', 'in', course.id),
            ], order='name asc')

            if course.forum_id:
                forum_ids |= course.forum_id
                forum_ids = forum_ids.sorted(key=lambda forum: forum.name or '')

            if forum_ids:
                post_ids = request.env['forum.post'].search([
                    ('forum_id', 'in', forum_ids.ids),
                    ('parent_id', '=', False),
                ], order='create_date desc')
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
