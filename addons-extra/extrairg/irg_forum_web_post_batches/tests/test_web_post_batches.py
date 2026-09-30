from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestForumWebPostBatches(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_group = cls.env.ref('base.group_user')
        portal_group = cls.env.ref('base.group_portal')
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Web Post Batches Internal',
            'login': 'web-post-batches-internal@example.test',
            'email': 'web-post-batches-internal@example.test',
            'groups_id': [(6, 0, user_group.ids)],
        })
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Web Post Batches Portal',
            'login': 'web-post-batches-portal@example.test',
            'email': 'web-post-batches-portal@example.test',
            'groups_id': [(6, 0, portal_group.ids)],
        })
        cls.course = cls.env['op.course'].create({
            'name': 'Web Post Batches Course',
            'code': 'WPBC',
        })
        cls.other_course = cls.env['op.course'].create({
            'name': 'Web Post Batches Other',
            'code': 'WPBO',
        })
        today = fields.Date.today()
        cls.batch_a = cls.env['op.batch'].create({
            'name': 'Lote A',
            'code': 'WPBA',
            'course_id': cls.course.id,
            'start_date': today,
            'end_date': today,
        })
        cls.batch_b = cls.env['op.batch'].create({
            'name': 'Lote B',
            'code': 'WPBB',
            'course_id': cls.course.id,
            'start_date': today,
            'end_date': today,
        })
        cls.inactive_batch = cls.env['op.batch'].create({
            'name': 'Lote Inactivo',
            'code': 'WPBI',
            'course_id': cls.course.id,
            'start_date': today,
            'end_date': today,
            'active': False,
        })
        cls.other_batch = cls.env['op.batch'].create({
            'name': 'Lote Otro',
            'code': 'WPBX',
            'course_id': cls.other_course.id,
            'start_date': today,
            'end_date': today,
        })
        forum_model = cls.env['forum.forum']
        forum_vals = {
            'name': 'Web Post Batches Forum',
            'irg_course_id': cls.course.id,
        }
        empty_forum_vals = {'name': 'Web Post Batches No Course'}
        if 'email_notify_enabled' in forum_model._fields:
            forum_vals['email_notify_enabled'] = False
            empty_forum_vals['email_notify_enabled'] = False
        cls.forum = forum_model.create(forum_vals)
        cls.forum_without_course = forum_model.create(empty_forum_vals)
        cls.forum.write({'karma_ask': 0, 'karma_answer': 0})
        cls.forum_without_course.write({'karma_ask': 0, 'karma_answer': 0})

    def _create_post(self, user, forum, batch_ids=None, parent=None):
        context = {}
        if batch_ids is not None:
            context['irg_visibility_batch_ids'] = batch_ids
        values = {
            'name': 'Tema de prueba',
            'content': '<p>Contenido</p>',
            'forum_id': forum.id,
        }
        if parent:
            values['parent_id'] = parent.id
            values['name'] = 'Respuesta de prueba'
        return self.env['forum.post'].with_user(user).with_context(**context).create(values)

    def test_internal_user_stores_selected_course_batches(self):
        post = self._create_post(
            self.internal_user,
            self.forum,
            [self.batch_a.id, str(self.batch_b.id)],
        )
        self.assertEqual(
            set(post.sudo().visibility_batch_ids.ids),
            {self.batch_a.id, self.batch_b.id},
        )

    def test_internal_user_without_selection_leaves_field_empty(self):
        post = self._create_post(self.internal_user, self.forum)
        self.assertFalse(post.visibility_batch_ids)

    def test_invalid_batches_are_discarded(self):
        post = self._create_post(
            self.internal_user,
            self.forum,
            [self.other_batch.id, self.inactive_batch.id, 0, 'no-es-id', self.batch_a.id],
        )
        self.assertEqual(post.sudo().visibility_batch_ids.ids, [self.batch_a.id])

    def test_only_invalid_batches_leave_field_empty(self):
        post = self._create_post(
            self.internal_user,
            self.forum,
            [self.other_batch.id, self.inactive_batch.id],
        )
        self.assertFalse(post.visibility_batch_ids)

    def test_portal_user_cannot_apply_posted_batches(self):
        post = self._create_post(
            self.portal_user,
            self.forum,
            [self.batch_a.id, self.batch_b.id],
        )
        self.assertFalse(post.visibility_batch_ids)

    def test_reply_does_not_copy_batch_context(self):
        parent = self._create_post(self.internal_user, self.forum, [self.batch_a.id])
        reply = self._create_post(
            self.internal_user,
            self.forum,
            [self.batch_b.id],
            parent=parent,
        )
        self.assertFalse(reply.visibility_batch_ids)
        self.assertEqual(reply.parent_id, parent)

    def test_batch_list_is_active_batches_of_the_forum_course(self):
        batches = self.forum._irg_web_post_batches()
        self.assertEqual(set(batches.ids), {self.batch_a.id, self.batch_b.id})
        self.assertFalse(self.forum_without_course._irg_web_post_batches())

    def test_selector_view_is_limited_to_internal_users(self):
        view = self.env.ref('irg_forum_web_post_batches.new_question_batch_selector')
        self.assertIn("has_group('base.group_user')", view.arch_db)
        self.assertIn('irg_visibility_batch_ids', view.arch_db)
        self.assertEqual(view.inherit_id, self.env.ref('website_forum.new_question'))
