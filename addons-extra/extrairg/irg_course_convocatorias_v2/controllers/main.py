# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.irg_op_subject_visibility.controllers.main import SubjectVisibilitySlides


class CourseConvocatoriasSlides(SubjectVisibilitySlides):

    @http.route([
        '/slides/<model("slide.channel"):channel>',
        '/slides/<model("slide.channel"):channel>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=SubjectVisibilitySlides.sitemap_slide)
    def channel(self, channel, category=None, tag=None, page=1, slide_category=None,
                uncategorized=False, sorting=None, search=None, **kw):

        is_internal_user = request.env.user.has_group('base.group_user')
        if not is_internal_user:
            # Case 1: Channel is HomeClass and student is Online modality
            if channel.irg_online_channel_id:
                if channel._irg_is_online_student_for_channel():
                    return request.redirect('/slides/%s' % channel.irg_online_channel_id.id)

            # Case 2: Channel is Online clone and student is NOT Online modality (meaning HomeClass)
            elif channel.irg_homeclass_channel_id:
                if not channel.irg_homeclass_channel_id._irg_is_online_student_for_channel():
                    return request.redirect('/slides/%s' % channel.irg_homeclass_channel_id.id)

        return super(CourseConvocatoriasSlides, self).channel(
            channel,
            category=category,
            tag=tag,
            page=page,
            slide_category=slide_category,
            uncategorized=uncategorized,
            sorting=sorting,
            search=search,
            **kw
        )

    @http.route([
        '/slides/slide/<model("slide.slide"):slide>',
    ], type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        is_internal_user = request.env.user.has_group('base.group_user')
        if not is_internal_user:
            channel = slide.channel_id
            # Case 1: Slide is HomeClass and student is Online modality
            if channel.irg_online_channel_id:
                if channel._irg_is_online_student_for_channel():
                    clone_slide = request.env['slide.slide'].sudo().search([
                        ('channel_id', '=', channel.irg_online_channel_id.id),
                        ('irg_original_slide_id', '=', slide.id)
                    ], limit=1)
                    if clone_slide:
                        return request.redirect('/slides/slide/%s' % clone_slide.id)
                    else:
                        # Fallback if slide is not cloned yet: redirect to clone channel homepage
                        return request.redirect('/slides/%s' % channel.irg_online_channel_id.id)

            # Case 2: Slide is Online clone and student is NOT Online modality (meaning HomeClass)
            elif channel.irg_homeclass_channel_id:
                if not channel.irg_homeclass_channel_id._irg_is_online_student_for_channel():
                    if slide.irg_original_slide_id:
                        return request.redirect('/slides/slide/%s' % slide.irg_original_slide_id.id)
                    else:
                        # Fallback if original slide link is missing: redirect to HomeClass channel homepage
                        return request.redirect('/slides/%s' % channel.irg_homeclass_channel_id.id)

        return super(CourseConvocatoriasSlides, self).slide_view(slide, **kwargs)
