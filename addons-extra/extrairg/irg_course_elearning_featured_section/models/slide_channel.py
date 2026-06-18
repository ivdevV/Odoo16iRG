# -*- coding: utf-8 -*-

from markupsafe import Markup

from odoo import fields, models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    nbr_certification = fields.Integer(string='Certification Slides', store=True)

    def irg_get_featured_course(self):
        """Return the first course that configures a featured block for this channel."""
        self.ensure_one()
        course_model = self.env['op.course'].sudo()

        # If this is an online clone, look up the subjects on the main HomeClass channel
        channel = self
        if hasattr(self, 'irg_homeclass_channel_id') and self.irg_homeclass_channel_id:
            channel = self.irg_homeclass_channel_id

        subjects = channel.sudo().op_subject_ids

        courses = course_model.search([
            ('subject_ids', 'in', subjects.ids),
            ('irg_featured_section_enabled', '=', True),
        ], order='id', limit=1) if subjects else course_model.browse()

        if not courses and 'slide_channel_ids' in course_model._fields:
            courses = course_model.search([
                ('slide_channel_ids', 'in', channel.id),
                ('irg_featured_section_enabled', '=', True),
            ], order='id', limit=1)

        return courses

    def irg_get_featured_section_values(self):
        self.ensure_one()
        course = self.irg_get_featured_course()
        if not course:
            return {}
        if not (
            course.irg_featured_section_title
            or course.irg_featured_section_body
            or course.irg_featured_section_embed_code
        ):
            return {}
        return {
            'course': course,
            'title': course.irg_featured_section_title,
            'body': Markup(course.irg_featured_section_body or ''),
            'embed_code': Markup(course.irg_featured_section_embed_code or ''),
            'url': course.irg_featured_section_url,
            'button_label': course.irg_featured_section_button_label or 'Ver más',
        }


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    nbr_certification = fields.Integer(string='Certification', store=True)
