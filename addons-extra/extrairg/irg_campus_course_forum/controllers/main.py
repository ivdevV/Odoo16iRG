from odoo import http
from odoo.http import request

from odoo.addons.isep_website_custom.controllers.main import DashboardPortal


class DashboardPortalCampusForum(DashboardPortal):

    @http.route(['/campus/course/<int:course_id>'], type='http', auth="user", website=True)
    def view_user_profile_course(self, course_id, **post):
        response = super().view_user_profile_course(course_id, **post)

        course = request.env['op.course'].browse(course_id)
        forum = course.forum_id if course.exists() else request.env['forum.forum']
        post_ids = request.env['forum.post']

        if forum:
            post_ids = request.env['forum.post'].search([
                ('forum_id', '=', forum.id),
                ('parent_id', '=', False),
            ], order='create_date desc')

        if hasattr(response, 'qcontext'):
            response.qcontext.update({
                'course_forum': forum,
                'course_forum_post_ids': post_ids,
            })

        return response
