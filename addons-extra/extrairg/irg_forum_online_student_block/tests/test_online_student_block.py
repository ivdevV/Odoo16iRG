# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestForumOnlineStudentBlock(TransactionCase):

    def setUp(self):
        super().setUp()
        self.User = self.env['res.users']
        self.Partner = self.env['res.partner']
        self.Course = self.env['op.course']
        self.Batch = self.env['op.batch']
        self.Student = self.env['op.student']
        self.Admission = self.env['op.admission']
        self.Forum = self.env['forum.forum']
        self.Post = self.env['forum.post']

        self.course = self.Course.create({'name': 'Curso Forum Online Block'})
        self.master_course = self.Course.create({'name': 'Master HC Forum Online Block'})
        self.online_batch = self._create_batch('IAONL2601')
        self.homeclass_batch = self._create_batch('IAHC2606')
        self.master_homeclass_batch = self._create_batch('MIAHC2606', self.master_course)
        self.master_online_batch = self._create_batch('MIAMONL2601')
        self.free_master_online_batch = self._create_batch('MBIAMONL2601')

        self.campus_forum = self.Forum.create({
            'name': 'Foro Campus Online Block',
            'visibility_course_ids': [(6, 0, [self.course.id])],
        })
        self.global_forum = self.Forum.create({'name': 'Foro Global Online Block'})
        self.master_hc_forum = self.Forum.create({
            'name': 'Foro Master HC Online Block',
            'visibility_course_ids': [(6, 0, [self.master_course.id])],
        })

    def _create_batch(self, code, course=None):
        course = course or self.course
        return self.Batch.create({
            'name': code,
            'code': code,
            'course_id': course.id,
        })

    def _create_user_for_batch(self, code, batch):
        partner = self.Partner.create({
            'name': code,
            'email': '%s@example.com' % code.lower(),
        })
        user = self.User.create({
            'name': code,
            'login': '%s@example.com' % code.lower(),
            'partner_id': partner.id,
            'groups_id': [(4, self.env.ref('base.group_portal').id)],
        })
        student = self.Student.create({
            'user_id': user.id,
            'partner_id': partner.id,
        })
        self.Admission.create({
            'course_id': self.course.id,
            'batch_id': batch.id,
            'student_id': student.id,
            'partner_id': partner.id,
        })
        user.invalidate_cache()
        return user

    def test_online_student_sees_only_global_forums(self):
        user = self._create_user_for_batch('online-user', self.online_batch)

        self.assertTrue(user.irg_forum_online_blocked)
        visible_forums = self.Forum.forums_visible_for(user)

        self.assertIn(self.global_forum, visible_forums)
        self.assertNotIn(self.campus_forum, visible_forums)

    def test_online_student_cannot_publish_topic_or_reply(self):
        user = self._create_user_for_batch('online-publisher', self.online_batch)
        existing_post = self.Post.sudo().create({
            'name': 'Existing campus topic',
            'forum_id': self.campus_forum.id,
            'content': 'Existing content',
        })

        with self.assertRaises(UserError):
            self.Post.with_user(user).create({
                'name': 'Blocked topic',
                'forum_id': self.campus_forum.id,
                'content': 'Blocked content',
            })

        with self.assertRaises(UserError):
            self.Post.with_user(user).create({
                'name': 'Blocked reply',
                'parent_id': existing_post.id,
                'content': 'Blocked reply content',
            })

    def test_online_student_is_removed_from_notification_recipients(self):
        online_user = self._create_user_for_batch('online-recipient', self.online_batch)
        homeclass_user = self._create_user_for_batch('hc-recipient', self.homeclass_batch)
        self.campus_forum.message_subscribe(partner_ids=[
            online_user.partner_id.id,
            homeclass_user.partner_id.id,
        ])

        recipients = self.campus_forum._get_notification_recipients()

        self.assertNotIn(online_user.partner_id, recipients)
        self.assertIn(homeclass_user.partner_id, recipients)

    def test_homeclass_and_monl_batches_are_not_blocked(self):
        cases = [
            self.homeclass_batch,
            self.master_homeclass_batch,
            self.master_online_batch,
            self.free_master_online_batch,
        ]
        for batch in cases:
            user = self._create_user_for_batch('user-%s' % batch.code.lower(), batch)
            self.assertFalse(user.irg_forum_online_blocked, batch.code)

            visible_forums = self.Forum.forums_visible_for(user)
            expected_forum = self.master_hc_forum if batch.course_id == self.master_course else self.campus_forum
            self.assertIn(expected_forum, visible_forums, batch.code)

    def test_mixed_online_student_keeps_unrelated_master_hc_forum(self):
        user = self._create_user_for_batch('mixed-student', self.online_batch)
        student = self.Student.search([('user_id', '=', user.id)], limit=1)
        self.Admission.create({
            'course_id': self.master_course.id,
            'batch_id': self.master_homeclass_batch.id,
            'student_id': student.id,
            'partner_id': user.partner_id.id,
        })
        user.invalidate_cache()

        visible_forums = self.Forum.forums_visible_for(user)
        self.assertNotIn(self.campus_forum, visible_forums)
        self.assertIn(self.master_hc_forum, visible_forums)

    def test_system_user_is_not_blocked(self):
        user = self._create_user_for_batch('system-online', self.online_batch)
        user.write({'groups_id': [(4, self.env.ref('base.group_system').id)]})

        self.assertFalse(self.Forum._irg_user_blocks_campus_forums(user))