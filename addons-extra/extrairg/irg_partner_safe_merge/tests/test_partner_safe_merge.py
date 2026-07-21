import json
import threading

from odoo import Command, api, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.service import model as service_model
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "irg_partner_safe_merge")
class TestPartnerSafeMerge(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.Wizard = cls.env["irg.partner.safe.merge.wizard"]
        cls.master = cls.Partner.create(
            {
                "name": "Camila Comercial",
                "email": "camila@example.com",
                "phone": "+34 600 111 222",
                "city": "Madrid",
            }
        )
        cls.source = cls.Partner.create(
            {
                "name": "Camila Alumna",
                "email": " CAMILA@example.com ",
                "phone": "600111222",
                "street": "Calle Uno",
            }
        )
        cls.non_admin = cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Merge operator",
                "login": "merge-operator-tests",
                "email": "operator@example.com",
                "groups_id": [Command.set([cls.env.ref("base.group_user").id])],
            }
        )

    def _wizard(self, master=None, source=None):
        return self.Wizard.create_from_selection(
            [(master or self.master).id, (source or self.source).id]
        )

    def _choose_master_conflicts(self, wizard):
        for conflict in wizard.conflict_ids.filtered("requires_choice"):
            conflict.choice = "master"

    def _finalize_preview(self, wizard):
        wizard.action_preview()
        self._choose_master_conflicts(wizard)
        wizard.action_preview()
        self.assertTrue(wizard.preview_ready)

    def _academic_fixture(self, suffix):
        course = self.env["op.course"].create(
            {"name": "Collision course %s" % suffix, "code": "COL-%s" % suffix}
        )
        batch = self.env["op.batch"].create(
            {
                "name": "Collision batch %s" % suffix,
                "code": "COLB-%s" % suffix,
                "course_id": course.id,
                "end_date": "2027-12-31",
            }
        )
        product = self.env["product.product"].create(
            {"name": "Collision product %s" % suffix, "type": "service"}
        )
        register = self.env["op.admission.register"].create(
            {
                "name": "Collision register %s" % suffix,
                "course_id": course.id,
                "product_id": product.id,
                "min_count": 1,
            }
        )
        return course, batch, register

    def _admission(self, partner, course, batch, register, suffix):
        return self.env["op.admission"].create(
            {
                "name": "Collision admission %s" % suffix,
                "first_name": "Collision",
                "last_name": suffix,
                "email": partner.email,
                "birth_date": "2000-01-01",
                "gender": "f",
                "course_id": course.id,
                "batch_id": batch.id,
                "register_id": register.id,
                "partner_id": partner.id,
            }
        )

    def _create_committed_concurrency_case(self, inverse=False):
        registry = self.env.registry
        admin_user = self.env.ref("base.user_admin")
        with registry.cursor() as setup_cr:
            admin_env = api.Environment(setup_cr, admin_user.id, {})
            self.assertFalse(admin_env.su)
            Partner = admin_env["res.partner"]
            partners = Partner.create(
                [
                    {
                        "name": "Concurrent safe merge",
                        "email": "concurrent-safe-merge@example.com",
                        "phone": "+34 600 123 987",
                    },
                    {
                        "name": "Concurrent safe merge",
                        "email": "concurrent-safe-merge@example.com",
                        "phone": "+34 600 123 987",
                    },
                ]
            )
            Wizard = admin_env["irg.partner.safe.merge.wizard"]
            first = Wizard.create_from_selection(partners.ids)
            first.action_preview()
            first.confirmation_checked = True
            second = Wizard.create_from_selection(partners.ids)
            if inverse:
                second.action_swap()
            second.action_preview()
            second.confirmation_checked = True
            setup = {
                "admin_user_id": admin_user.id,
                "master_id": first.master_partner_id.id,
                "source_id": first.source_partner_id.id,
                "wizard_ids": (first.id, second.id),
            }
            setup_cr.commit()
        return setup

    def _cleanup_committed_concurrency_case(self, setup):
        registry = self.env.registry
        with registry.cursor() as cleanup_cr:
            cleanup_env = api.Environment(cleanup_cr, setup["admin_user_id"], {})
            wizard_ids = tuple(setup["wizard_ids"])
            cleanup_cr.execute(
                "DELETE FROM irg_partner_safe_merge_wizard_conflict "
                "WHERE wizard_id IN %s",
                (wizard_ids,),
            )
            cleanup_cr.execute(
                "DELETE FROM irg_partner_safe_merge_wizard WHERE id IN %s",
                (wizard_ids,),
            )
            cleanup_cr.execute(
                "DELETE FROM irg_partner_safe_merge_audit WHERE origin_partner_id = %s",
                (setup["source_id"],),
            )
            source = cleanup_env["res.partner"].with_context(active_test=False).browse(
                setup["source_id"]
            )
            if source.irg_merged_into_partner_id:
                source.with_context(_irg_safe_merge_service=True).sudo().write(
                    {"irg_merged_into_partner_id": False}
                )
            if not source.active:
                source.sudo().write({"active": True})
            cleanup_env["res.partner"].with_context(active_test=False).browse(
                [setup["master_id"], setup["source_id"]]
            ).unlink()
            cleanup_cr.commit()
        with registry.cursor() as verify_cr:
            verify_env = api.Environment(verify_cr, setup["admin_user_id"], {})
            self.assertFalse(
                verify_env["res.partner"].with_context(active_test=False).search_count(
                    [("id", "in", [setup["master_id"], setup["source_id"]])]
                )
            )

    def _run_concurrent_confirmations(self, inverse=False):
        setup = self._create_committed_concurrency_case(inverse=inverse)
        registry = self.env.registry
        lock_acquired = threading.Event()
        release_first = threading.Event()
        second_attempted = threading.Event()
        first_done = threading.Event()
        second_done = threading.Event()
        results = []
        errors = []

        def confirm(wizard_id, hold_locks, attempted, done):
            try:
                with registry.cursor() as worker_cr:
                    worker_env = api.Environment(
                        worker_cr, setup["admin_user_id"], {}
                    )
                    first_attempt = True

                    def request():
                        nonlocal first_attempt
                        worker_cr.execute("SET LOCAL statement_timeout = '10s'")
                        wizard = worker_env[
                            "irg.partner.safe.merge.wizard"
                        ].browse(wizard_id)
                        if hold_locks and first_attempt:
                            wizard._lock_generated_plan()
                            wizard._lock_partners()
                            lock_acquired.set()
                            if not release_first.wait(5):
                                raise AssertionError(
                                    "Timed out waiting to release first merge"
                                )
                        elif not hold_locks:
                            attempted.set()
                        first_attempt = False
                        return wizard.action_confirm()

                    result = service_model.retrying(request, worker_env)
                    results.append(result["res_id"])
            except Exception as error:  # thread result is asserted by the parent test
                errors.append(error)
            finally:
                done.set()

        first = threading.Thread(
            target=confirm,
            args=(setup["wizard_ids"][0], True, threading.Event(), first_done),
            name="safe-merge-first-confirmation",
        )
        second = threading.Thread(
            target=confirm,
            args=(setup["wizard_ids"][1], False, second_attempted, second_done),
            name="safe-merge-second-confirmation",
        )
        try:
            first.start()
            self.assertTrue(lock_acquired.wait(5))
            second.start()
            self.assertTrue(second_attempted.wait(5))
            self.assertFalse(second_done.wait(0.25))
            release_first.set()
            first.join(10)
            second.join(10)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertTrue(first_done.is_set())
            self.assertTrue(second_done.is_set())
            with registry.cursor() as assert_cr:
                assert_env = api.Environment(assert_cr, setup["admin_user_id"], {})
                source = assert_env["res.partner"].with_context(
                    active_test=False
                ).browse(setup["source_id"])
                outcome = {
                    "results": list(results),
                    "audit_count": assert_env[
                        "irg.partner.safe.merge.audit"
                    ].search_count([("origin_partner_id", "=", setup["source_id"])]),
                    "source_active": source.active,
                    "merged_into_id": source.irg_merged_into_partner_id.id,
                    "master_id": setup["master_id"],
                }
            return setup, outcome, errors
        finally:
            release_first.set()
            if first.is_alive():
                first.join(10)
            if second.is_alive():
                second.join(10)
            self._cleanup_committed_concurrency_case(setup)

    def test_open_preview_and_confirm_require_system_administrator(self):
        selected = (self.master | self.source).with_user(self.non_admin)
        with self.assertRaises(AccessError):
            selected.action_irg_safe_merge()
        with self.assertRaises(AccessError):
            self.Wizard.with_user(self.non_admin).create_from_selection(selected.ids)
        wizard = self._wizard().with_user(self.non_admin)
        with self.assertRaises(AccessError):
            wizard.action_preview()
        with self.assertRaises(AccessError):
            wizard.action_confirm()

    def test_selection_identity_company_hierarchy_and_archived_guards(self):
        with self.assertRaises(ValidationError):
            self.Wizard.create_from_selection([self.master.id])
        with self.assertRaises(ValidationError):
            self.Wizard.create_from_selection([self.master.id, self.master.id])

        unrelated = self.Partner.create({"name": "Other", "email": "other@example.com"})
        with self.assertRaises(ValidationError):
            self.Wizard.create_from_selection([self.master.id, unrelated.id])

        child = self.Partner.create(
            {"name": "Child", "email": self.master.email, "parent_id": self.master.id}
        )
        with self.assertRaises(ValidationError):
            self.Wizard.create_from_selection([self.master.id, child.id])

        company = self.env["res.company"].create({"name": "Other merge company"})
        other_company = self.Partner.create(
            {"name": "Company scoped", "email": self.master.email, "company_id": company.id}
        )
        scoped_master = self.master.copy({"company_id": self.env.company.id})
        with self.assertRaises(ValidationError):
            self.Wizard.create_from_selection([scoped_master.id, other_company.id])

        archived = self.master.copy({"active": False})
        with self.assertRaises(ValidationError):
            self.Wizard.create_from_selection([archived.id, self.source.id])

    def test_preview_skips_abstract_partner_model_without_id(self):
        abstract_model = self.env["hr.employee.base"]
        self.assertFalse(abstract_model._auto)
        self.assertNotIn("id", abstract_model._fields)
        wizard = self._wizard()
        wizard.action_preview()
        self.assertTrue(wizard.exists())

    def test_recommendation_is_explainable_and_admin_can_swap(self):
        sale = self.env["sale.order"].create({"partner_id": self.master.id})
        sale.action_confirm()
        wizard = self._wizard()
        self.assertEqual(wizard.master_partner_id, self.master)
        self.assertIn("sale", wizard.recommendation_reason.lower())
        wizard.action_swap()
        self.assertEqual(wizard.master_partner_id, self.source)
        self.assertEqual(wizard.source_partner_id, self.master)

    def test_scalar_empty_copy_and_explicit_nonempty_conflict(self):
        wizard = self._wizard()
        wizard.action_preview()
        city = wizard.conflict_ids.filtered(lambda line: line.field_name == "city")
        street = wizard.conflict_ids.filtered(lambda line: line.field_name == "street")
        self.assertEqual(city.choice, "master")
        self.assertEqual(street.choice, "source")
        self.assertFalse(street.requires_choice)

        source = self.source.copy({"city": "Barcelona"})
        wizard = self.Wizard.create_from_selection([self.master.id, source.id])
        wizard.action_preview()
        city = wizard.conflict_ids.filtered(lambda line: line.field_name == "city")
        self.assertTrue(city.requires_choice)
        city.choice = False
        wizard.confirmation_checked = True
        with self.assertRaises(ValidationError):
            wizard.action_confirm()

    def test_camila_graph_preserves_leads_and_moves_user_student(self):
        leads = self.env["crm.lead"]
        for index in range(4):
            leads |= leads.create(
                {"name": "Camila lead %s" % index, "partner_id": self.source.id}
            )
        user = self.env["res.users"].with_context(
            no_reset_password=True, mail_channel_nosubscribe=True
        ).create(
            {
                "name": self.source.name,
                "login": "camila-safe-merge-tests",
                "partner_id": self.source.id,
            }
        )
        student = self.env["op.student"].create(
            {"partner_id": self.source.id, "user_id": user.id, "gender": "f"}
        )
        orders = self.env["sale.order"]
        orders |= orders.create(
            {
                "partner_id": self.master.id,
                "state": "sale",
                "client_order_ref": "CAMILA-MASTER",
            }
        )
        orders |= orders.create(
            {
                "partner_id": self.source.id,
                "state": "sale",
                "client_order_ref": "CAMILA-SOURCE",
            }
        )
        # isep_form_data creates a res.card as an unconditional sale-order side
        # effect. Cards on the source are an intentional blocker and are not
        # part of this transfer fixture, so remove only those synthetic rows.
        self.env["res.card"].with_context(active_test=False).search(
            [("partner_id", "in", orders.mapped("partner_id").ids)]
        ).unlink()
        schedule = self.env["sale.subscription.schedule"].create(
            {
                "order_id": orders[0].id,
                "term_number": 1,
                "term_label": "1",
                "date_due": fields.Date.today(),
                "date_schedule": fields.Date.today(),
                "amount_recurring_taxinc": 100.0,
            }
        )
        product = self.env["product.product"].create(
            {"name": "Camila course fee", "type": "service"}
        )
        admissions = self.env["op.admission"]
        for index in range(2):
            course = self.env["op.course"].create(
                {"name": "Camila course %s" % index, "code": "CAMILA-%s" % index}
            )
            batch = self.env["op.batch"].create(
                {
                    "name": "Camila batch %s" % index,
                    "code": "CB-%s" % index,
                    "course_id": course.id,
                    "end_date": "2027-12-31",
                }
            )
            register = self.env["op.admission.register"].create(
                {
                    "name": "Camila register %s" % index,
                    "course_id": course.id,
                    "product_id": product.id,
                    "min_count": 1,
                }
            )
            admissions |= admissions.create(
                {
                    "name": "Camila Alumna",
                    "first_name": "Camila",
                    "last_name": "Alumna",
                    "email": self.source.email,
                    "birth_date": "2000-01-01",
                    "gender": "f",
                    "course_id": course.id,
                    "batch_id": batch.id,
                    "register_id": register.id,
                    "partner_id": self.source.id,
                }
            )
        message = self.source.message_post(body="Camila merge message")
        activity = self.source.activity_schedule(
            "mail.mail_activity_data_todo", summary="Camila merge activity"
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": "camila-safe-merge",
                "type": "url",
                "url": "https://example.invalid/camila",
                "res_model": "res.partner",
                "res_id": self.source.id,
            }
        )
        lead_ids = leads.ids
        order_ids = orders.ids
        admission_ids = admissions.ids

        wizard = self._wizard()
        self._finalize_preview(wizard)
        wizard.confirmation_checked = True
        audit = self.env["irg.partner.safe.merge.audit"].browse(
            wizard.action_confirm()["res_id"]
        )

        self.assertEqual(user.partner_id, self.master)
        self.assertEqual(student.partner_id, self.master)
        self.assertEqual(leads.ids, lead_ids)
        self.assertEqual(leads.mapped("partner_id"), self.master)
        self.assertEqual(orders.ids, order_ids)
        self.assertEqual(orders.mapped("partner_id"), self.master)
        self.assertEqual(admissions.ids, admission_ids)
        self.assertEqual(admissions.mapped("partner_id"), self.master)
        self.assertEqual(schedule.order_id, orders[0])
        self.assertEqual(schedule.partner_id, self.master)
        self.assertEqual(message.res_id, self.master.id)
        self.assertEqual(activity.res_id, self.master.id)
        self.assertEqual(attachment.res_id, self.master.id)
        self.assertFalse(self.source.active)
        self.assertEqual(self.source.irg_merged_into_partner_id, self.master)
        self.assertEqual(audit.origin_partner_id, self.source)

    def test_source_bank_record_blocks_preview(self):
        bank = self.env["res.bank"].create({"name": "Safe merge test bank"})
        self.env["res.partner.bank"].create(
            {"acc_number": "ES-SAFE-MERGE-TEST", "partner_id": self.source.id, "bank_id": bank.id}
        )
        with self.assertRaises(ValidationError):
            self._wizard().action_preview()

    def test_source_account_move_blocks_preview(self):
        journal = self.env["account.journal"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("type", "=", "general"),
            ],
            limit=1,
        )
        if not journal:
            journal = self.env["account.journal"].create(
                {
                    "name": "Safe merge test journal",
                    "code": "IRGM",
                    "type": "general",
                    "company_id": self.env.company.id,
                }
            )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "partner_id": self.source.id,
                "date": fields.Date.today(),
                "ref": "Safe merge accounting blocker",
            }
        )
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.partner_id, self.source)
        with self.assertRaisesRegex(
            ValidationError,
            r"account\.move\.(commercial_partner_id|partner_id)",
        ):
            self._wizard().action_preview()

    def test_duplicate_entities_block_preview(self):
        duplicate_master = self.master.copy()
        duplicate_source = self.source.copy()
        duplicate_user_master = self.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {"name": "Master user", "login": "master-safe-merge", "partner_id": duplicate_master.id}
        )
        duplicate_user_source = self.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {"name": "Source user", "login": "source-safe-merge", "partner_id": duplicate_source.id}
        )
        self.assertTrue(duplicate_user_master and duplicate_user_source)
        with self.assertRaises(ValidationError):
            self._wizard(duplicate_master, duplicate_source).action_preview()

    def test_category_and_follower_union_preserves_subtypes(self):
        category = self.env["res.partner.category"].create({"name": "Merge category"})
        self.master.category_id = [Command.link(category.id)]
        self.source.category_id = [Command.link(category.id)]
        subtype_comment = self.env.ref("mail.mt_comment")
        subtype_note = self.env.ref("mail.mt_note")
        self.master.message_subscribe([self.non_admin.partner_id.id], [subtype_comment.id])
        self.source.message_subscribe([self.non_admin.partner_id.id], [subtype_note.id])

        wizard = self._wizard()
        self._finalize_preview(wizard)
        wizard.confirmation_checked = True
        wizard.action_confirm()

        follower = self.env["mail.followers"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", self.master.id),
                ("partner_id", "=", self.non_admin.partner_id.id),
            ]
        )
        self.assertEqual(follower.subtype_ids, subtype_comment | subtype_note)
        self.assertIn(category, self.master.category_id)

    def test_preview_hash_detects_changes_and_lock_order_is_stable(self):
        wizard = self._wizard()
        self._finalize_preview(wizard)
        old_hash = wizard.preview_hash
        self.source.phone = "600333444"
        wizard.confirmation_checked = True
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        self.assertEqual(wizard.preview_hash, old_hash)
        self.assertEqual(wizard._ordered_partner_ids(), sorted([self.master.id, self.source.id]))

    def test_injected_failures_rollback_each_mutation_phase(self):
        phases = ("scalars", "user", "student", "relations", "m2m", "chatter", "archive")
        for phase in phases:
            master = self.master.copy()
            source = self.source.copy({"street": "Rollback source street"})
            master_street_before = master.street
            user = self.env["res.users"].with_context(
                no_reset_password=True, mail_channel_nosubscribe=True
            ).create(
                {
                    "name": source.name,
                    "login": "rollback-%s-safe-merge" % phase,
                    "partner_id": source.id,
                }
            )
            student = self.env["op.student"].create(
                {"partner_id": source.id, "user_id": user.id, "gender": "f"}
            )
            lead = self.env["crm.lead"].create(
                {"name": "Rollback %s" % phase, "partner_id": source.id}
            )
            category = self.env["res.partner.category"].create(
                {"name": "Rollback %s" % phase}
            )
            source.category_id = [Command.link(category.id)]
            source.message_subscribe(
                [self.non_admin.partner_id.id], [self.env.ref("mail.mt_comment").id]
            )
            source_follower_id = self.env["mail.followers"].search(
                [
                    ("res_model", "=", "res.partner"),
                    ("res_id", "=", source.id),
                    ("partner_id", "=", self.non_admin.partner_id.id),
                ],
                limit=1,
            ).id
            self.assertTrue(source_follower_id)
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "rollback-%s" % phase,
                    "type": "url",
                    "url": "https://example.invalid/%s" % phase,
                    "res_model": "res.partner",
                    "res_id": source.id,
                }
            )
            wizard = self.Wizard.create_from_selection([master.id, source.id])
            self._finalize_preview(wizard)
            wizard.confirmation_checked = True
            with self.assertRaises(UserError):
                with self.cr.savepoint():
                    wizard.with_context(irg_safe_merge_fail_after_phase=phase).action_confirm()
            self.env.invalidate_all()
            master = self.Partner.browse(master.id)
            source = self.Partner.with_context(active_test=False).browse(source.id)
            user = self.env["res.users"].with_context(active_test=False).browse(user.id)
            student = self.env["op.student"].browse(student.id)
            lead = self.env["crm.lead"].browse(lead.id)
            attachment = self.env["ir.attachment"].browse(attachment.id)
            source_follower = self.env["mail.followers"].browse(source_follower_id)
            self.assertEqual(master.street, master_street_before)
            self.assertTrue(source.active)
            self.assertFalse(source.irg_merged_into_partner_id)
            self.assertEqual(user.partner_id, source)
            self.assertEqual(student.partner_id, source)
            self.assertEqual(lead.partner_id, source)
            self.assertNotIn(category, master.category_id)
            self.assertIn(category, source.category_id)
            self.assertEqual(attachment.res_id, source.id)
            self.assertTrue(source_follower.exists())
            self.assertEqual(source_follower.res_model, "res.partner")
            self.assertEqual(source_follower.res_id, source.id)
            self.assertFalse(
                self.env["irg.partner.safe.merge.audit"].search_count(
                    [("origin_partner_id", "=", source.id)]
                )
            )

    def test_double_confirmation_is_idempotent_and_inverse_is_blocked(self):
        wizard = self._wizard()
        self._finalize_preview(wizard)
        wizard.confirmation_checked = True
        audit = wizard.action_confirm()["res_id"]
        self.assertEqual(wizard.action_confirm()["res_id"], audit)
        with self.assertRaises(ValidationError):
            self.Wizard.create_from_selection([self.source.id, self.master.id])

    def test_merged_source_and_audit_are_immutable(self):
        wizard = self._wizard()
        self._finalize_preview(wizard)
        wizard.confirmation_checked = True
        audit = self.env["irg.partner.safe.merge.audit"].browse(
            wizard.action_confirm()["res_id"]
        )
        with self.assertRaises(AccessError):
            self.source.write({"irg_merged_into_partner_id": False})
        with self.assertRaises(ValidationError):
            self.source.with_context(active_test=False).write({"active": True})
        with self.assertRaises(ValidationError):
            self.source.with_context(active_test=False).unlink()
        with self.assertRaises(AccessError):
            audit.write({"actions_json": "{}"})
        with self.assertRaises(AccessError):
            audit.unlink()
        with self.assertRaises(AccessError):
            self.env["irg.partner.safe.merge.audit"].create(
                {
                    "master_partner_id": self.master.id,
                    "origin_partner_id": self.source.id,
                    "actor_id": self.env.user.id,
                    "preview_hash": "rpc-tampering",
                }
            )

    def test_rpc_tampering_cannot_inject_unknown_scalar_field(self):
        wizard = self._wizard()
        wizard.action_preview()
        conflict = wizard.conflict_ids[:1]
        with self.assertRaises(ValidationError):
            conflict.write({"field_name": "company_id"})

    def test_rpc_context_cannot_forge_generated_preview_state(self):
        admin_user = self.env.ref("base.user_admin")
        admin_env = api.Environment(self.cr, admin_user.id, {})
        self.assertTrue(admin_user.has_group("base.group_system"))
        self.assertFalse(admin_env.su)
        wizard = admin_env["irg.partner.safe.merge.wizard"].browse(self._wizard().id)
        with self.assertRaises(AccessError):
            wizard.with_context(_irg_safe_merge_wizard_service=True).write(
                {"preview_hash": "forged", "preview_ready": True}
            )

    def test_user_and_student_without_exact_link_are_blocked(self):
        master = self.master.copy()
        source = self.source.copy()
        self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": source.name,
                "login": "unlinked-student-safe-merge",
                "partner_id": source.id,
            }
        )
        self.env["op.student"].create({"partner_id": source.id, "gender": "f"})
        with self.assertRaises(ValidationError):
            self._wizard(master, source).action_preview()

    def test_two_students_are_isolated_from_other_blockers(self):
        master = self.master.copy()
        source = self.source.copy()
        self.env["op.student"].create(
            {"partner_id": master.id, "gender": "f"}
        )
        self.env["op.student"].create(
            {"partner_id": source.id, "gender": "f"}
        )
        with self.assertRaises(ValidationError):
            self._wizard(master, source).action_preview()

    def test_payment_and_accounting_relations_are_explicit_block_policies(self):
        for model_name, field_name in (
            ("res.partner.bank", "partner_id"),
            ("account.move", "partner_id"),
            ("account.move.line", "partner_id"),
            ("account.payment", "partner_id"),
            ("payment.transaction", "partner_id"),
            ("payment.token", "partner_id"),
        ):
            if model_name not in self.env or field_name not in self.env[model_name]._fields:
                continue
            self.assertEqual(
                self.Wizard._classify_relation(
                    (model_name, field_name), self.env[model_name]._fields[field_name]
                ),
                "block",
            )

    def test_allowlisted_elearning_transient_is_locked_and_transferred(self):
        transient = self.env["op.admission.elearning.wizard"].create(
            {"partner_id": self.source.id}
        )
        wizard = self._wizard()
        self._finalize_preview(wizard)
        wizard.confirmation_checked = True
        wizard.action_confirm()
        self.assertEqual(transient.partner_id, self.master)

    def test_scalar_decision_change_invalidates_final_plan_hash(self):
        source = self.source.copy({"city": "Barcelona"})
        wizard = self._wizard(self.master, source)
        self._finalize_preview(wizard)
        original_hash = wizard.preview_hash
        city = wizard.conflict_ids.filtered(lambda line: line.field_name == "city")
        city.choice = "source"
        wizard.confirmation_checked = True
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        self.assertEqual(wizard.preview_hash, original_hash)

    def test_same_and_inverse_plans_use_the_same_partner_lock_order(self):
        same = self._wizard()
        inverse = self._wizard()
        inverse.action_swap()
        expected = sorted([self.master.id, self.source.id])
        self.assertEqual(same._ordered_partner_ids(), expected)
        self.assertEqual(inverse._ordered_partner_ids(), expected)

    def test_concurrent_same_confirmation_is_idempotent(self):
        _setup, outcome, errors = self._run_concurrent_confirmations()
        self.assertFalse(errors)
        self.assertEqual(len(outcome["results"]), 2)
        self.assertEqual(len(set(outcome["results"])), 1)
        self.assertEqual(outcome["audit_count"], 1)
        self.assertFalse(outcome["source_active"])
        self.assertEqual(outcome["merged_into_id"], outcome["master_id"])

    def test_concurrent_inverse_confirmation_blocks_loser(self):
        _setup, outcome, errors = self._run_concurrent_confirmations(inverse=True)
        self.assertEqual(len(outcome["results"]), 1)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValidationError)
        self.assertEqual(outcome["audit_count"], 1)
        self.assertFalse(outcome["source_active"])
        self.assertEqual(outcome["merged_into_id"], outcome["master_id"])

    def test_unknown_direct_many2many_relation_blocks(self):
        if "calendar.event" not in self.env:
            self.skipTest("calendar.event is not installed in this runtime")
        self.env["calendar.event"].create(
            {
                "name": "Unknown M2M safe merge blocker",
                "start": fields.Datetime.now(),
                "stop": fields.Datetime.add(fields.Datetime.now(), hours=1),
                "partner_ids": [Command.link(self.source.id)],
            }
        )
        with self.assertRaises(ValidationError):
            self._wizard().action_preview()

    def test_unknown_many2one_relation_blocks_independently(self):
        self.Partner.create(
            {
                "name": "Dependent third contact",
                "email": "dependent@example.com",
                "parent_id": self.source.id,
            }
        )
        with self.assertRaises(ValidationError):
            self._wizard().action_preview()

    def test_audit_contains_before_and_after_partner_snapshots(self):
        wizard = self._wizard()
        self._finalize_preview(wizard)
        wizard.confirmation_checked = True
        audit = self.env["irg.partner.safe.merge.audit"].browse(
            wizard.action_confirm()["res_id"]
        )
        before = json.loads(audit.before_snapshot_json)
        after = json.loads(audit.after_snapshot_json)
        self.assertTrue(before["source"]["active"])
        self.assertFalse(after["source"]["active"])
        self.assertEqual(after["source"]["merged_into_id"], self.master.id)

    def test_admission_business_collision_blocks(self):
        course, batch, register = self._academic_fixture("ADM")
        self._admission(self.master, course, batch, register, "master")
        self._admission(self.source, course, batch, register, "source")
        with self.assertRaises(ValidationError):
            self._wizard().action_preview()

    def test_gradebook_business_collision_blocks(self):
        course, batch, _register = self._academic_fixture("GRADE")
        self.env["appisep.gradebook.summary"].create(
            [
                {
                    "student_id": self.master.id,
                    "course_id": course.id,
                    "batch_id": batch.id,
                },
                {
                    "student_id": self.source.id,
                    "course_id": course.id,
                    "batch_id": batch.id,
                },
            ]
        )
        with self.assertRaises(ValidationError):
            self._wizard().action_preview()

    def test_sale_business_collision_blocks(self):
        SaleOrder = self.env["sale.order"]
        SaleOrder.create(
            {"partner_id": self.master.id, "client_order_ref": "DUPLICATE-REF"}
        )
        SaleOrder.create(
            {"partner_id": self.source.id, "client_order_ref": "DUPLICATE-REF"}
        )
        with self.assertRaises(ValidationError):
            self._wizard().action_preview()

    def test_schedule_business_collision_blocks(self):
        SaleOrder = self.env["sale.order"]
        orders = SaleOrder.create({"partner_id": self.master.id})
        orders |= SaleOrder.create({"partner_id": self.source.id})
        for order in orders:
            self.env["sale.subscription.schedule"].create(
                {
                    "order_id": order.id,
                    "term_number": 1,
                    "term_label": "1",
                    "date_due": fields.Date.today(),
                    "date_schedule": fields.Date.today(),
                    "amount_recurring_taxinc": 100.0,
                }
            )
        with self.assertRaises(ValidationError):
            self._wizard().action_preview()
