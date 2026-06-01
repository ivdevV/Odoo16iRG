# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.osv import expression


class ForumForum(models.Model):
    _inherit = 'forum.forum'

    def _irg_is_campus_course_forum(self):
        self.ensure_one()
        return bool(self.visibility_batch_ids or self.visibility_course_ids)

    @api.model
    def _visibility_domain_for_user(self, user, course=None):
        domain = super()._visibility_domain_for_user(user, course=course)
        if self._irg_user_blocks_campus_forums(user):
            # sudo: read computed academic block fields even when the current visitor is a portal user.
            user = user.sudo()
            restriction_domain = []
            if user.irg_forum_online_blocked_batch_ids:
                restriction_domain.append((
                    'visibility_batch_ids',
                    'not in',
                    user.irg_forum_online_blocked_batch_ids.ids,
                ))
            if user.irg_forum_online_blocked_course_ids:
                restriction_domain.append((
                    'visibility_course_ids',
                    'not in',
                    user.irg_forum_online_blocked_course_ids.ids,
                ))
            domain = expression.AND([
                domain,
                restriction_domain,
            ])
        return domain

    @api.model
    def _irg_user_blocks_campus_forums(self, user):
        if not user or user._is_public() or user.has_group('base.group_public'):
            return False
        if user.has_group('base.group_system'):
            return False
        # sudo: access-control evaluation must read computed enrollment data for portal users.
        return bool(user.sudo().irg_forum_online_blocked)

    def _irg_filter_online_blocked_partners(self, partners):
        self.ensure_one()
        if not partners or not self._irg_is_campus_course_forum():
            return partners

        # sudo: notification filtering maps partners to users without exposing user records to the frontend.
        users = self.env['res.users'].sudo().search([
            ('partner_id', 'in', partners.ids),
            ('active', '=', True),
        ])
        blocked_partners = users.filtered(
            lambda user: self._irg_user_is_blocked_from_forum(user)
        ).mapped('partner_id')
        return partners - blocked_partners

    def _irg_user_is_blocked_from_forum(self, user):
        self.ensure_one()
        if not self._irg_user_blocks_campus_forums(user):
            return False
        if not self._irg_is_campus_course_forum():
            return False

        # sudo: compare forum visibility metadata with computed user block fields for an access decision only.
        forum = self.sudo()
        user = user.sudo()
        blocked_batch_ids = set(user.irg_forum_online_blocked_batch_ids.ids)
        blocked_course_ids = set(user.irg_forum_online_blocked_course_ids.ids)
        forum_batch_ids = set(forum.visibility_batch_ids.ids)
        forum_course_ids = set(forum.visibility_course_ids.ids)
        return bool(
            (blocked_batch_ids and forum_batch_ids & blocked_batch_ids)
            or (blocked_course_ids and forum_course_ids & blocked_course_ids)
        )

    def _get_notification_recipients(self, exclude_partner=None):
        partners = super()._get_notification_recipients(exclude_partner=exclude_partner)
        return self._irg_filter_online_blocked_partners(partners)