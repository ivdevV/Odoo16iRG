# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.irg_batch_slide_restrictions.controllers.main import (
    WebsiteSlidesBatchRestrictions,
)
from odoo.http import request


class WebsiteSlidesPracticeRestrictions(WebsiteSlidesBatchRestrictions):
    @http.route(
        ['/slides/slide/<model("slide.slide"):slide>'],
        type='http',
        auth='public',
        website=True,
        sitemap=True,
    )
    def slide_view(self, slide, **kwargs):
        if slide.sudo()._irg_effective_practice_type():
            user = request.env.user
            if user._is_public():
                return request.redirect(
                    '/web/login?redirect=/slides/slide/%s' % slide.id
                )
            if not slide.is_user_allowed_by_practice_type(user):
                return request.render(
                    'irg_practice_slide_restrictions.slide_practice_restriction_error',
                    {'slide': slide},
                )
        return super().slide_view(slide, **kwargs)

    def _get_slide_detail(self, slide):
        values = super()._get_slide_detail(slide)
        user = request.env.user
        blocked = set()
        if not user._is_public() and slide.channel_id:
            channel_slides = slide.channel_id.slide_ids.sudo()
            first = channel_slides[:1]
            student = first._irg_student_for_user(user) if first else request.env['op.student']
            courses = (
                first._irg_courses_for_channel() if first else request.env['op.course']
            )
            for item in channel_slides:
                if not item.is_user_allowed_by_practice_type(
                    user, student=student, courses=courses
                ):
                    blocked.add(item.id)
        values['practice_blocked_slide_ids'] = blocked
        return values
