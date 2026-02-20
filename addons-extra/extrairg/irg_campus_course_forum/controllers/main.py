from odoo import http
from odoo.http import request

from odoo.addons.isep_website_custom_inh.controllers.main import DashboardPortalInh


class DashboardPortalCampusForum(DashboardPortalInh):

    @http.route(['/campus/course/<int:course_id>'], type='http', auth="user", website=True)
    def view_user_profile_course(self, course_id, **post):
        response = super().view_user_profile_course(course_id, **post)

        course = request.env['op.course'].sudo().browse(course_id)
        forum_ids = request.env['forum.forum'].sudo()
        post_ids = request.env['forum.post'].sudo()
        posts_by_forum_id = {}
        user = request.env.user

        if course.exists():
            user_batch_ids = set(user.op_batch_ids.ids)
            admission_batch_ids = request.env['op.admission'].sudo().search([
                ('partner_id', '=', user.partner_id.id),
                ('course_id', '=', course.id),
                ('batch_id', '!=', False),
            ]).mapped('batch_id').ids
            user_batch_ids.update(admission_batch_ids)

            forum_ids = request.env['forum.forum'].sudo().search([
                ('visibility_course_ids', 'in', course.id),
            ], order='name asc')

            if user_batch_ids:
                forum_ids |= request.env['forum.forum'].sudo().search([
                    ('visibility_batch_ids', 'in', list(user_batch_ids)),
                    '|',
                    ('visibility_course_ids', '=', False),
                    ('visibility_course_ids', 'in', course.id),
                ], order='name asc')

            if course.forum_id:
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

                post_ids = request.env['forum.post'].sudo().search(post_domain, order='create_date desc')
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
