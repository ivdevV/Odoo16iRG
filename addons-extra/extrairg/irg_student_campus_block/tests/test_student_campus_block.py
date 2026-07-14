# -*- coding: utf-8 -*-

from lxml import etree
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install", "irg_student_campus_block")
class TestStudentCampusBlock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.back_office_user = new_test_user(
            cls.env,
            login="campus.block.admin@example.test",
            groups="openeducat_core.group_op_back_office_admin",
            name="Campus Block Administrator",
        )
        cls.faculty_user = new_test_user(
            cls.env,
            login="campus.block.faculty@example.test",
            groups="openeducat_core.group_op_faculty",
            name="Campus Faculty",
        )

    def _create_student(self, suffix, user_groups="base.group_portal"):
        partner = self.env["res.partner"].create({
            "name": "Campus Student %s" % suffix,
            "email": "campus.student.%s@example.test" % suffix,
        })
        user = False
        if user_groups is not None:
            user = new_test_user(
                self.env,
                login=partner.email,
                groups=user_groups,
                name=partner.name,
            )
            user.partner_id = partner
        student = self.env["op.student"].create({
            "partner_id": partner.id,
            "first_name": "Campus",
            "last_name": "Student %s" % suffix,
            "gender": "o",
            "user_id": user.id if user else False,
        })
        return student, user

    def test_block_deactivates_portal_user_and_updates_computed_state(self):
        student, user = self._create_student("block")

        student.with_user(self.back_office_user).action_block_campus_access()

        self.assertFalse(user.with_context(active_test=False).active)
        self.assertTrue(student.irg_campus_blocked)

    def test_unblock_reactivates_portal_user_and_updates_computed_state(self):
        student, user = self._create_student("unblock")
        user.active = False

        student.with_user(self.back_office_user).action_unblock_campus_access()

        self.assertTrue(user.with_context(active_test=False).active)
        self.assertFalse(student.irg_campus_blocked)

    def test_actions_are_idempotent_against_stale_requests(self):
        student, user = self._create_student("idempotent")

        student.with_user(self.back_office_user).action_block_campus_access()
        messages_after_block = len(student.message_ids)
        student.with_user(self.back_office_user).action_block_campus_access()

        self.assertFalse(user.with_context(active_test=False).active)
        self.assertEqual(len(student.message_ids), messages_after_block)

        student.with_user(self.back_office_user).action_unblock_campus_access()
        messages_after_unblock = len(student.message_ids)
        student.with_user(self.back_office_user).action_unblock_campus_access()

        self.assertTrue(user.with_context(active_test=False).active)
        self.assertEqual(len(student.message_ids), messages_after_unblock)

    def test_missing_user_is_rejected(self):
        student, _user = self._create_student("without-user", user_groups=None)

        with self.assertRaisesRegex(UserError, "usuario portal"):
            student.with_user(self.back_office_user).action_block_campus_access()

    def test_effective_change_posts_chatter_as_real_operator(self):
        student, user = self._create_student("chatter")
        before = student.message_ids

        student.with_user(self.back_office_user).action_block_campus_access()

        message = (student.message_ids - before).sorted("id")[-1]
        self.assertEqual(message.author_id, self.back_office_user.partner_id)
        self.assertIn(self.back_office_user.name, message.body)
        self.assertIn(user.name, message.body)
        self.assertIn("bloqueado", message.body.lower())

    def test_faculty_cannot_call_action_through_orm(self):
        student, user = self._create_student("faculty-denied")

        with self.assertRaises(AccessError):
            student.with_user(self.faculty_user).action_block_campus_access()

        self.assertTrue(user.active)

    def test_internal_target_is_rejected(self):
        student, user = self._create_student("internal", "base.group_user")

        with self.assertRaisesRegex(UserError, "portal"):
            student.with_user(self.back_office_user).action_block_campus_access()

        self.assertTrue(user.active)

    def test_public_non_portal_target_is_rejected(self):
        student, user = self._create_student("public", "base.group_public")

        with self.assertRaisesRegex(UserError, "portal"):
            student.with_user(self.back_office_user).action_block_campus_access()

        self.assertTrue(user.active)

    def test_blocked_linked_user_stays_inactive_during_optional_rematriculation(self):
        admission_model = self.env["op.admission"]
        if not hasattr(admission_model, "_ensure_portal_user"):
            self.skipTest("Optional manual confirmation wizard is not installed")

        student, user = self._create_student("rematriculation")
        student.with_user(self.back_office_user).action_block_campus_access()
        admission = admission_model.new({
            "name": student.name,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "gender": student.gender,
            "email": student.email,
            "partner_id": student.partner_id.id,
            "student_id": student.id,
        })

        admission._ensure_portal_user()

        self.assertEqual(student.user_id.with_context(active_test=False), user)
        self.assertFalse(user.with_context(active_test=False).active)

    def test_optional_rematriculation_exposes_unlinked_archived_user_collision(self):
        admission_model = self.env["op.admission"]
        if not hasattr(admission_model, "_ensure_portal_user"):
            self.skipTest("Optional manual confirmation wizard is not installed")

        student, user = self._create_student("rematriculation-unlinked")
        student.with_user(self.back_office_user).action_block_campus_access()
        student.user_id = False
        admission = admission_model.new({
            "name": student.name,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "gender": student.gender,
            "email": student.email,
            "partner_id": student.partner_id.id,
            "student_id": student.id,
        })

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            admission._ensure_portal_user()

        self.assertFalse(student.user_id)
        self.assertFalse(user.with_context(active_test=False).active)

    def test_view_exposes_explicit_restricted_actions_and_ribbon(self):
        view = self.env.ref("irg_student_campus_block.view_op_student_form_campus_block")
        arch = etree.fromstring(view.arch_db.encode())

        for action in (
            "action_block_campus_access",
            "action_unblock_campus_access",
        ):
            buttons = arch.xpath("//button[@name='%s']" % action)
            self.assertEqual(len(buttons), 1)
            self.assertEqual(
                buttons[0].get("groups"),
                "openeducat_core.group_op_back_office_admin",
            )
            self.assertTrue(buttons[0].get("confirm"))
        ribbons = arch.xpath(
            "//widget[@name='web_ribbon'][@title='Campus bloqueado']"
        )
        self.assertEqual(len(ribbons), 1)
        self.assertIn("('active', '=', False)", ribbons[0].get("attrs", ""))
