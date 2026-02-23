from odoo.tests import TransactionCase


class TestForumVisibility(TransactionCase):
    def setUp(self):
        super().setUp()
        self.User = self.env['res.users']
        self.Forum = self.env['forum.forum']
        self.Batch = self.env['op.batch']
        self.Course = self.env['op.course']
        self.Admission = self.env['op.admission']
        self.Student = self.env['op.student']
        self.StudentCourse = self.env['op.student.course']

        # create user/partner
        partner = self.env['res.partner'].create({'name': 'Test User'})
        self.user = self.User.create({'name': 'test', 'login': 'test',
                                      'partner_id': partner.id})

        # course + batch
        self.course = self.Course.create({'name': 'Dummy Course'})
        self.batch = self.Batch.create({'name': 'Dummy Batch', 'course_id': self.course.id})

    def test_batch_only_forum(self):
        # user has no batches initially; should see only public forums
        public = self.Forum.create({'name': 'public forum'})
        private = self.Forum.create({'name': 'private forum',
                                     'visibility_batch_ids': [(6, 0, [self.batch.id])]})
        # user without batch sees only the public forum via helper
        shown = self.Forum.forums_visible_for(self.user)
        self.assertIn(public, shown)
        self.assertNotIn(private, shown)

        # now add the batch to the user through admission
        student = self.Student.create({'user_id': self.user.id, 'partner_id': self.user.partner_id.id})
        self.Admission.create({'course_id': self.course.id,
                               'batch_id': self.batch.id,
                               'student_id': student.id})

        # recompute fields
        self.user.invalidate_cache()
        self.assertTrue(self.batch in self.user.forum_effective_batch_ids)

        shown2 = self.Forum.forums_visible_for(self.user)
        self.assertIn(private, shown2)

    def test_empty_batch_domain(self):
        # if a forum has no visibility_batch_ids it should be visible to everyone
        f = self.Forum.create({'name': 'everyone'})
        self.assertIn(f, self.Forum.forums_visible_for(self.user))
