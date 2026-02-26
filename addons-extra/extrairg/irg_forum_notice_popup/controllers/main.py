from odoo import http
from odoo.http import request

from odoo.addons.irg_campus_course_forum.controllers.main import DashboardPortalCampusForum


class ForumNoticePopupController(DashboardPortalCampusForum):

    NOTICE_KEYWORDS = ('aviso', 'anuncio', 'announcement')

    def _post_title(self, post):
        title = ''
        if 'name' in post._fields and post.name:
            title = post.name
        elif 'title' in post._fields and post.title:
            title = post.title
        return (title or '').strip()

    def _post_content_preview(self, post):
        raw_content = ''
        for field_name in ('content', 'description', 'body'):
            if field_name in post._fields:
                value = getattr(post, field_name)
                if value:
                    raw_content = value
                    break
        plain = (raw_content or '').replace('<br>', ' ').replace('<br/>', ' ').replace('\n', ' ')
        return plain.strip()[:220]

    def _is_notice_post(self, post):
        title = self._post_title(post).lower()
        if any(keyword in title for keyword in self.NOTICE_KEYWORDS):
            return True

        if 'tag_ids' in post._fields and post.tag_ids:
            tag_names = ' '.join(post.tag_ids.mapped('name')).lower()
            if any(keyword in tag_names for keyword in self.NOTICE_KEYWORDS):
                return True

        return False

    @http.route('/campus/course/<int:course_id>/forum_notice_popup', type='json', auth='user', website=True)
    def forum_notice_popup(self, course_id, **kwargs):
        user = request.env.user
        course = request.env['op.course'].sudo().browse(course_id)
        if not course.exists() or not user or user._is_public():
            return {'notice': False}

        user_batch_ids = self._get_user_batch_ids_for_course(user, course)
        forum_domain = self._forum_visibility_domain_for_user(course, user_batch_ids)
        forums = request.env['forum.forum'].sudo().search(forum_domain)
        if not forums:
            return {'notice': False}

        post_model = request.env['forum.post'].sudo()
        post_domain = [
            ('forum_id', 'in', forums.ids),
            ('parent_id', '=', False),
        ]
        if 'state' in post_model._fields:
            post_domain.append(('state', '=', 'active'))
        if 'active' in post_model._fields:
            post_domain.append(('active', '=', True))
        if 'visibility_batch_ids' in post_model._fields:
            if user_batch_ids:
                post_domain += ['|', ('visibility_batch_ids', '=', False), ('visibility_batch_ids', 'in', list(user_batch_ids))]
            else:
                post_domain += [('visibility_batch_ids', '=', False)]

        posts = post_model.search(post_domain, order='create_date desc', limit=40)
        notice_post = next((post for post in posts if self._is_notice_post(post)), False)

        if not notice_post:
            return {'notice': False}

        website_url = ''
        if 'website_url' in notice_post._fields and notice_post.website_url:
            website_url = notice_post.website_url
        elif notice_post.forum_id:
            website_url = f'/forum/{notice_post.forum_id.id}'

        return {
            'notice': {
                'id': notice_post.id,
                'title': self._post_title(notice_post),
                'preview': self._post_content_preview(notice_post),
                'forum_name': notice_post.forum_id.name if notice_post.forum_id else '',
                'url': website_url,
            }
        }
