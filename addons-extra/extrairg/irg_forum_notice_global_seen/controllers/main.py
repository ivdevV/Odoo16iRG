from odoo import http
from odoo.http import request

from odoo.addons.irg_forum_notice_popup.controllers.main import (
    ForumNoticePopupController,
)


class IrgForumNoticeGlobalSeenController(ForumNoticePopupController):

    def _global_seen_model(self):
        return request.env['irg.forum.notice.global.seen'].sudo()

    def _is_seen(self, user_id, course_id, post_id):
        del course_id
        return self._global_seen_model()._irg_is_seen(user_id, post_id)

    def _mark_seen(self, user_id, course_id, post_id):
        del course_id
        return self._global_seen_model()._irg_mark_seen(user_id, post_id)

    def _find_notice_for_user_global(self, user):
        notice_post, course_id = super()._find_notice_for_user_global(user)
        if notice_post and self._is_seen(
            user.id, course_id, notice_post.id
        ):
            return False, False
        return notice_post, course_id

    def _mark_visible_notice_seen(self, notice_id):
        user = request.env.user
        if not user or user._is_public() or not notice_id:
            return {'ok': False}
        try:
            notice_id = int(notice_id)
        except (TypeError, ValueError):
            return {'ok': False}

        post = request.env['forum.post'].sudo().browse(notice_id).exists()
        if not post or not post._is_visible_for_user(user):
            return {'ok': False}

        self._global_seen_model()._irg_mark_seen(user.id, post.id)
        return {'ok': True}

    @http.route()
    def forum_notice_popup(self, course_id, **kwargs):
        return super().forum_notice_popup(course_id, **kwargs)

    @http.route()
    def forum_notice_popup_any_campus(self, **kwargs):
        return super().forum_notice_popup_any_campus(**kwargs)

    @http.route()
    def forum_notice_popup_seen(self, course_id, notice_id=None, **kwargs):
        del course_id, kwargs
        return self._mark_visible_notice_seen(notice_id)

    @http.route()
    def forum_notice_popup_seen_any_campus(
        self, course_id=None, notice_id=None, **kwargs
    ):
        del course_id, kwargs
        return self._mark_visible_notice_seen(notice_id)
