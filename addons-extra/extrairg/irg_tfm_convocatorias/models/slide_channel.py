from odoo import models

from .op_student_course import irg_parse_tfm_batch_eligibility


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def _irg_tfm_base_channel(self):
        self.ensure_one()
        channel = self.sudo()
        return channel.irg_homeclass_channel_id or channel

    def _irg_tfm_family_channels(self):
        self.ensure_one()
        base = self._irg_tfm_base_channel()
        family = base
        online = base.irg_online_channel_id
        if online and online.irg_homeclass_channel_id == base:
            family |= online
        return family

    def _irg_tfm_effective_channel(self, enrollment):
        """Select the channel from the exact TFM enrollment, never admission."""
        self.ensure_one()
        enrollment.ensure_one()
        base = self._irg_tfm_base_channel()
        family = self._irg_tfm_family_channels()
        if self.id not in family.ids:
            return self.browse()
        eligibility = irg_parse_tfm_batch_eligibility(enrollment.batch_id.code)
        if not eligibility:
            return self.browse()
        modality = eligibility[0]
        if modality == 'ONL':
            online = base.irg_online_channel_id
            if online and online in family:
                return online
            return self.browse()
        if modality == 'HC':
            return base
        return self.browse()

    def _irg_tfm_is_configured_family(self):
        self.ensure_one()
        family_ids = self.sudo()._irg_tfm_expand_family_channels().ids
        return bool(self.env['op.course'].sudo().search_count([
            ('activate_tesis', '=', True),
            ('irg_tfm_channel_id', 'in', family_ids),
        ]))

    def _irg_tfm_route_for_user(self, user):
        """Return one owned active thesis and its exact channel, or fail closed."""
        self.ensure_one()
        empty_thesis = self.env['tesis.model'].browse()
        empty_channel = self.browse()
        if not user or user._is_public() or user.has_group('base.group_user'):
            return empty_thesis, empty_channel

        channel = self.sudo()
        base = channel._irg_tfm_base_channel()
        family = channel._irg_tfm_family_channels()
        if channel.id not in family.ids:
            return empty_thesis, empty_channel

        students = self.env['op.student'].sudo().with_context(active_test=False).search([
            ('user_id', '=', user.id),
        ], limit=2)
        if len(students) != 1 or not students.active:
            return empty_thesis, empty_channel

        theses = self.env['tesis.model'].sudo().with_context(active_test=False).search([
            ('course_id.student_id', '=', students.id),
            ('course_id.student_id.user_id', '=', user.id),
            ('course_id.course_id.irg_tfm_channel_id', 'in', family.ids),
            ('irg_tfm_activated_at', '!=', False),
        ])
        candidates = []
        for thesis in theses:
            configured = thesis.course_id.course_id.irg_tfm_channel_id
            if not configured or configured._irg_tfm_base_channel().id != base.id:
                continue
            effective = configured._irg_tfm_effective_channel(thesis.course_id)
            if effective and effective in family:
                candidates.append((thesis, effective))
        if len(candidates) != 1:
            return empty_thesis, empty_channel
        thesis, effective = candidates[0]
        if not thesis.irg_tfm_convocation_id.active:
            return empty_thesis, empty_channel
        return thesis, effective

    def _irg_bootstrap_prepare_slide_values(self, source, online_channel):
        values = super()._irg_bootstrap_prepare_slide_values(source, online_channel)
        values.pop('irg_tfm_convocation_ids', None)
        if source.is_category and source.irg_tfm_convocation_ids:
            values['irg_tfm_convocation_ids'] = [
                (6, 0, source.irg_tfm_convocation_ids.ids),
            ]
        return values

    def _irg_tfm_expand_family_channels(self):
        """Return the complete family, including broken inverse references."""
        Channel = self.env['slide.channel']
        family = self.exists()
        previous_ids = set()
        while set(family.ids) != previous_ids:
            previous_ids = set(family.ids)
            direct = family.mapped('irg_online_channel_id')
            direct |= family.mapped('irg_homeclass_channel_id')
            inverse = Channel.search([
                '|',
                ('irg_online_channel_id', 'in', list(previous_ids)),
                ('irg_homeclass_channel_id', 'in', list(previous_ids)),
            ])
            family |= direct | inverse
        return family

    def _irg_tfm_courses_for_family_lifecycle(self):
        return self.env['op.course'].search([
            ('activate_tesis', '=', True),
            ('irg_tfm_channel_id', 'in', self.ids),
        ])

    def _irg_tfm_theses_for_family_lifecycle(self):
        if not self:
            return self.env['tesis.model'].browse()
        return self.env['tesis.model'].search([
            ('course_id.course_id.irg_tfm_channel_id', 'in', self.ids),
            ('irg_tfm_activated_at', '!=', False),
        ])

    def _irg_tfm_reconcile_family_theses(self, theses):
        for thesis in theses.exists():
            thesis._irg_reconcile_tfm_membership()

    def write(self, values):
        family_fields = {'irg_online_channel_id', 'irg_homeclass_channel_id'}
        if not family_fields.intersection(values):
            return super().write(values)
        if not self.env.user.has_group('base.group_user'):
            return super().write(values)

        # Authorization is deliberately evaluated before the elevated family
        # traversal. External callers remain governed by the native ACL path.
        before_family = self.sudo()._irg_tfm_expand_family_channels()
        before_courses = before_family._irg_tfm_courses_for_family_lifecycle()
        before_theses = before_family._irg_tfm_theses_for_family_lifecycle()
        result = super().write(values)
        after_family = self.sudo().exists()._irg_tfm_expand_family_channels()
        after_courses = after_family._irg_tfm_courses_for_family_lifecycle()
        after_theses = after_family._irg_tfm_theses_for_family_lifecycle()
        if before_courses or after_courses:
            self._irg_tfm_reconcile_family_theses(before_theses | after_theses)
        return result

    def unlink(self):
        if not self.env.user.has_group('base.group_user'):
            return super().unlink()

        # As in write(), no sudo is reached before the authorization branch.
        before_family = self.sudo()._irg_tfm_expand_family_channels()
        before_courses = before_family._irg_tfm_courses_for_family_lifecycle()
        before_theses = before_family._irg_tfm_theses_for_family_lifecycle()
        result = super().unlink()
        if before_courses:
            self._irg_tfm_reconcile_family_theses(before_theses)
        return result
