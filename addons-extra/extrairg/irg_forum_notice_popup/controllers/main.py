import logging

from psycopg2 import IntegrityError

from odoo import fields, http
from odoo.http import request

from odoo.addons.irg_campus_course_forum.controllers.main import DashboardPortalCampusForum

_logger = logging.getLogger(__name__)


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

    def _seen_model(self):
        return request.env['irg.forum.notice.seen'].sudo()

    def _is_seen(self, user_id, course_id, post_id):
        return bool(self._seen_model().search_count([
            ('user_id', '=', user_id),
            ('course_id', '=', course_id),
            ('post_id', '=', post_id),
        ]))

    def _candidate_courses_for_user(self, user):
        user = user.sudo()
        course_ids = set(user.forum_effective_course_ids.ids)

        student_model = request.env['op.student'].sudo()
        student_course_model = request.env['op.student.course'].sudo()
        admission_model = request.env['op.admission'].sudo()

        students = student_model.search([
            '|',
            ('user_id', '=', user.id),
            ('partner_id', '=', user.partner_id.id),
        ])

        if students:
            sc_courses = student_course_model.search([
                ('student_id', 'in', students.ids),
                ('course_id', '!=', False),
                ('state', '!=', 'finished'),
            ]).mapped('course_id').ids
            course_ids.update(sc_courses)

        if 'op_batch_ids' in user._fields and 'course_id' in request.env['op.batch']._fields:
            course_ids.update(user.op_batch_ids.mapped('course_id').ids)

        adm_courses = admission_model.search([
            ('course_id', '!=', False),
            '|',
            ('partner_id', '=', user.partner_id.id),
            ('student_id', 'in', students.ids or [0]),
        ]).mapped('course_id').ids
        course_ids.update(adm_courses)

        if not course_ids:
            return request.env['op.course']
        return request.env['op.course'].sudo().browse(list(course_ids)).exists()

    def _find_notice_for_course(self, user, course):
        user_batch_ids = self._get_user_batch_ids_for_course(user, course)
        forum_domain = self._forum_visibility_domain_for_user(course, user_batch_ids)
        forums = request.env['forum.forum'].sudo().search(forum_domain)
        if not forums:
            return False

        post_model = request.env['forum.post'].sudo()
        post_domain = [
            ('forum_id', 'in', forums.ids),
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
        if 'excluded_visibility_batch_ids' in post_model._fields:
            if user_batch_ids:
                post_domain += ['|', ('excluded_visibility_batch_ids', '=', False), ('excluded_visibility_batch_ids', 'not in', list(user_batch_ids))]
            else:
                post_domain += [('excluded_visibility_batch_ids', '=', False)]

        posts = post_model.search(post_domain, order='create_date desc', limit=40)
        if hasattr(posts, '_filter_visible_for_user'):
            posts = posts._filter_visible_for_user(user, course=course)
        notice_post = next((post for post in posts if self._is_notice_post(post)), False)
        if not notice_post and posts:
            notice_post = posts[0]
        if not notice_post:
            return False

        if self._is_seen(user.id, course.id, notice_post.id):
            return False

        return notice_post

    def _notice_payload(self, notice_post, course_id):
        website_url = ''
        if 'website_url' in notice_post._fields and notice_post.website_url:
            website_url = notice_post.website_url
        elif notice_post.forum_id:
            website_url = f'/forum/{notice_post.forum_id.id}'

        return {
            'id': notice_post.id,
            'title': self._post_title(notice_post),
            'preview': self._post_content_preview(notice_post),
            'forum_name': notice_post.forum_id.name if notice_post.forum_id else '',
            'url': website_url,
            'course_id': course_id,
        }

    def _find_notice_for_user_global(self, user):
        forums = request.env['forum.forum'].search([])
        if not forums:
            return False, False

        post_model = request.env['forum.post']
        post_domain = [
            ('forum_id', 'in', forums.ids),
        ]
        if 'state' in post_model._fields:
            post_domain.append(('state', '=', 'active'))
        if 'active' in post_model._fields:
            post_domain.append(('active', '=', True))

        posts = post_model.search(post_domain, order='create_date desc', limit=40)
        if hasattr(posts, '_filter_visible_for_user'):
            posts = posts._filter_visible_for_user(user)
        if not posts:
            return False, False

        notice_post = next((post for post in posts if self._is_notice_post(post)), False)
        if not notice_post:
            notice_post = posts[0]

        forum_course = notice_post.forum_id.visibility_course_ids[:1]
        course_id = forum_course.id if forum_course else False
        if not course_id:
            user_courses = user.sudo().forum_effective_course_ids[:1]
            course_id = user_courses.id if user_courses else False

        if course_id and self._is_seen(user.id, course_id, notice_post.id):
            return False, False

        return notice_post, course_id

    def _mark_seen(self, user_id, course_id, post_id):
        seen_model = self._seen_model()
        seen = seen_model.search([
            ('user_id', '=', user_id),
            ('course_id', '=', course_id),
            ('post_id', '=', post_id),
        ], limit=1)
        if seen:
            seen.write({'seen_at': fields.Datetime.now()})
        else:
            try:
                with seen_model.env.cr.savepoint():
                    seen_model.create({
                        'user_id': user_id,
                        'course_id': course_id,
                        'post_id': post_id,
                    })
            except IntegrityError:
                _logger.debug('forum_notice_seen: duplicate record (race condition), ignoring.')

    @http.route('/campus/course/<int:course_id>/forum_notice_popup', type='json', auth='user', website=True)
    def forum_notice_popup(self, course_id, **kwargs):
        user = request.env.user
        course = request.env['op.course'].sudo().browse(course_id)
        if not course.exists() or not user or user._is_public():
            return {'notice': False}

        notice_post = self._find_notice_for_course(user, course)
        if not notice_post:
            return {'notice': False}

        return {'notice': self._notice_payload(notice_post, course.id)}

    @http.route('/campus/forum_notice_popup', type='json', auth='user', website=True)
    def forum_notice_popup_any_campus(self, **kwargs):
        user = request.env.user
        if not user or user._is_public():
            return {'notice': False}

        courses = self._candidate_courses_for_user(user)
        for course in courses:
            notice_post = self._find_notice_for_course(user, course)
            if notice_post:
                return {'notice': self._notice_payload(notice_post, course.id)}

        notice_post, course_id = self._find_notice_for_user_global(user)
        if notice_post:
            return {'notice': self._notice_payload(notice_post, course_id)}

        return {'notice': False}

    @http.route('/campus/course/<int:course_id>/forum_notice_popup_seen', type='json', auth='user', website=True)
    def forum_notice_popup_seen(self, course_id, notice_id=None, **kwargs):
        user = request.env.user
        if not user or user._is_public() or not notice_id:
            return {'ok': False}

        try:
            notice_id = int(notice_id)
        except Exception:
            return {'ok': False}

        post = request.env['forum.post'].sudo().browse(notice_id)
        if not post.exists():
            return {'ok': False}

        self._mark_seen(user.id, course_id, notice_id)
        return {'ok': True}

    @http.route('/campus/forum_notice_popup_seen', type='json', auth='user', website=True)
    def forum_notice_popup_seen_any_campus(self, course_id=None, notice_id=None, **kwargs):
        user = request.env.user
        if not user or user._is_public() or not notice_id or not course_id:
            return {'ok': False}

        try:
            notice_id = int(notice_id)
            course_id = int(course_id)
        except Exception:
            return {'ok': False}

        post = request.env['forum.post'].sudo().browse(notice_id)
        course = request.env['op.course'].sudo().browse(course_id)
        if not post.exists() or not course.exists():
            return {'ok': False}

        self._mark_seen(user.id, course_id, notice_id)
        return {'ok': True}
