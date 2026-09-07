import json
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import tagged
from odoo.addons.irg_enrollment_modification.tests.test_enrollment_change import TestEnrollmentChange as BaseCase


@tagged('post_install', '-at_install', 'irg_enrollment_modification_guard')
class TestEnrollmentGuard(BaseCase):
    def request(self, **vals):
        defaults = dict(change_batch=True, dest_batch_id=self.batch_dest.id)
        defaults.update(vals)
        action = self._wizard(self.academic, **defaults).action_create_request()
        return self.env['irg.enrollment.change'].browse(action['res_id'])

    def direct(self, **vals):
        defaults = dict(student_id=self.student.id,
                        student_course_id=self.student_course.id,
                        sale_order_id=self.sale_order.id,
                        change_batch=True, dest_batch_id=self.batch_dest.id)
        defaults.update(vals)
        return self.env['irg.enrollment.change'].create(defaults)

    def test_guard_stale_batch_is_permanently_blocked(self):
        request = self.request()
        other = self._create_batch('C', 'GUARD-C3', self.course)
        self.student_course.batch_id = other
        action = request.with_user(self.academic).action_approve_academic()
        self.assertEqual(self.student_course.batch_id, other)
        self.assertEqual(action['tag'], 'display_notification')
        self.assertTrue(request.irg_guard_blocked)
        self.assertFalse(request.final_attachment_id)
        self.assertEqual(request.state, 'submitted')
        self.student_course.batch_id = self.batch
        count = len(request.message_ids)
        request.action_approve_academic()
        self.assertEqual(self.student_course.batch_id, self.batch)
        self.assertEqual(len(request.message_ids), count)
        request.with_user(self.academic).action_refuse()
        self.assertEqual(request.state, 'refused')

    def test_guard_phone_is_irrelevant(self):
        request = self.request()
        self.student.phone = '123'
        request.with_user(self.academic).action_approve_academic()
        self.assertEqual(self.student_course.batch_id, self.batch_dest)
        self.assertEqual(request.state, 'done')

    def test_guard_server_captures_origins(self):
        request = self.direct(origin_batch_id=self.batch_dest.id,
                              origin_course_id=self.course_dest.id)
        self.assertEqual(request.origin_batch_id, self.batch)
        self.assertEqual(request.origin_course_id, self.course)

    def test_guard_direct_request_validation(self):
        for vals in [dict(change_batch=False), dict(dest_batch_id=False),
                     dict(dest_batch_id=self.batch_other_course.id),
                     dict(change_payment=True, sale_order_id=False),
                     dict(change_course=True, dest_course_id=self.course_dest.id)]:
            with self.subTest(vals=vals), self.assertRaises(ValidationError), self.cr.savepoint():
                self.direct(**vals)

    def test_guard_rejects_foreign_enrollment_and_order(self):
        foreign = self.env['op.student'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Foreign'}).id,
            'first_name': 'Foreign', 'last_name': 'Student', 'gender': 'o'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.direct(student_id=foreign.id)
        self.sale_order.student_id = foreign.partner_id
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.direct(change_payment=True, dest_payment_mode_id=self.pay_dest.id)

    def test_guard_explicit_student_allows_different_payer(self):
        self.sale_order.partner_id = self.env['res.partner'].create({'name': 'Payer'})
        request = self.direct(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.action_approve_academic()
        request.action_approve_finance()
        self.assertEqual(self.sale_order.payment_mode_id, self.pay_dest)

    def test_guard_write_protection_all_roles(self):
        request = self.request()
        for user in [self.academic, self.accountant, self.env.user]:
            for vals in [dict(state='done'), dict(academic_user_id=user.id),
                         dict(dest_batch_id=self.batch.id), dict(origin_batch_id=self.batch_dest.id),
                         dict(change_batch=False), dict(irg_guard_snapshot={}),
                         dict(irg_guard_blocked=False)]:
                with self.subTest(user=user.name, vals=vals), self.assertRaises(AccessError):
                    request.with_user(user).with_context(irg_guard_token=True).write(vals)

    def test_guard_context_defaults_cannot_create_approved_request(self):
        request = self.env['irg.enrollment.change'].with_context(
            default_state='done', default_academic_user_id=self.env.uid,
            default_irg_guard_snapshot={'version': 1},
            default_irg_guard_blocked=True).create({
                'student_id': self.student.id, 'student_course_id': self.student_course.id,
                'change_batch': True, 'dest_batch_id': self.batch_dest.id})
        self.assertEqual(request.state, 'submitted')
        self.assertFalse(request.academic_user_id)
        self.assertFalse(request.irg_guard_blocked)
        for vals in [dict(state='done'), dict(academic_user_id=self.env.uid), dict(irg_guard_snapshot={})]:
            with self.assertRaises(AccessError):
                self.direct(**vals)

    def test_guard_finance_preserves_external_academic_edit(self):
        request = self.request(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.with_user(self.academic).action_approve_academic()
        self.student_course.batch_id = self.batch
        action = request.with_user(self.accountant).action_approve_finance()
        self.assertEqual(self.sale_order.payment_mode_id, self.pay_origin)
        self.assertEqual(self.student_course.batch_id, self.batch)
        self.assertEqual(request.state, 'academic_approved')
        self.assertEqual(action['tag'], 'display_notification')

    def test_guard_payment_change_blocks_before_academic(self):
        request = self.request(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        self.sale_order.payment_mode_id = self.pay_dest
        request.action_approve_academic()
        self.assertEqual(self.student_course.batch_id, self.batch)
        self.assertEqual(request.state, 'submitted')

    def test_guard_modality_line_set_and_values(self):
        self.assertIn('x_studio_modalidad', self.env['sale.order.line']._fields)
        for mutation in ['insert', 'unlink', 'edit', 'move']:
            with self.subTest(mutation=mutation), self.cr.savepoint():
                order = self._create_sale_order(self.student.partner_id, self.course, self.pay_origin)
                request = self.direct(sale_order_id=order.id, change_modality=True, dest_modality='Homeclass')
                if mutation == 'insert':
                    order.order_line.copy({'order_id': order.id})
                elif mutation == 'unlink':
                    order.order_line.unlink()
                elif mutation == 'edit':
                    order.order_line.x_studio_modalidad = 'Presencial'
                else:
                    order.order_line.order_id = self.sale_order
                request.action_approve_academic()
                self.assertEqual(request.state, 'submitted')
                self.assertEqual(self.student_course.batch_id, self.batch)

    def test_guard_new_empty_origin_is_known(self):
        self.sale_order.payment_mode_id = False
        request = self.direct(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.action_approve_academic()
        request.action_approve_finance()
        self.assertEqual(self.sale_order.payment_mode_id, self.pay_dest)
        self.assertEqual(request.state, 'done')

    def test_guard_year_and_destination_relation(self):
        request = self.direct(change_year=True, dest_year_id=self.year_dest.id)
        self.student_course.academic_years_id = self.year_dest
        request.action_approve_academic()
        self.assertEqual(self.student_course.batch_id, self.batch)
        self.assertEqual(request.state, 'submitted')
        request = self.direct()
        self.batch_dest.course_id = self.course_dest
        request.action_approve_academic()
        self.assertEqual(self.student_course.batch_id, self.batch)
        self.assertEqual(request.state, 'submitted')

    def test_guard_retry_pdf_does_not_reapply(self):
        request = self.request()
        Document = type(self.env['irg.enrollment.change.document'])
        with patch.object(Document, 'build_pdf_bytes', side_effect=UserError('Converter unavailable')):
            request.action_approve_academic()
        self.student_course.batch_id = self.batch
        with patch.object(Document, 'build_pdf_bytes', return_value=b'%PDF-1.4\n%%EOF'):
            request.with_user(self.academic).action_retry_pdf()
        self.assertEqual(self.student_course.batch_id, self.batch)
        self.assertFalse(request.pdf_pending)
        self.assertTrue(request.final_attachment_id)

    def test_guard_legacy_preinstall(self):
        ids = json.loads(self.env['ir.config_parameter'].sudo().get_param('irg_guard_test_fixtures'))
        Change = self.env['irg.enrollment.change']
        for kind in ['submitted', 'missing', 'modality', 'academic_approved', 'done', 'refused']:
            request = Change.browse(ids[kind])
            self.assertFalse(request.irg_guard_snapshot)
            if kind in ['done', 'refused']:
                self.assertEqual(request.state, kind)
                continue
            if kind == 'academic_approved':
                request.action_approve_finance()
                self.assertEqual(request.state, 'done')
            else:
                request.action_approve_academic()
                self.assertEqual(request.state, 'done' if kind == 'submitted' else 'submitted')
                self.assertEqual(request.irg_guard_blocked, kind != 'submitted')

    def test_guard_finance_rules_are_not_bypassed_by_inspection(self):
        request = self.request(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.with_user(self.academic).action_approve_academic()
        self.assertFalse(self.env['op.student.course'].with_user(self.accountant).check_access_rights('read', raise_exception=False))
        self.env['ir.rule'].create({
            'name': 'Guard deny financial enrollment',
            'model_id': self.env['ir.model']._get_id('op.student.course'),
            'domain_force': "[('id', '!=', %d)]" % self.student_course.id,
        })
        with self.assertRaises(AccessError):
            request.with_user(self.accountant).action_approve_finance()
        self.assertEqual(self.sale_order.payment_mode_id, self.pay_origin)
        self.assertEqual(request.state, 'academic_approved')

    def test_guard_finance_conflict_does_not_disclose_academic_data(self):
        request = self.request(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.with_user(self.academic).action_approve_academic()
        other = self._create_batch('Confidential academic batch', 'GUARD-SECRET', self.course)
        self.student_course.batch_id = other
        action = request.with_user(self.accountant).action_approve_finance()
        for text in [request.irg_guard_conflict_detail, action['params']['message'], request.message_ids[0].body]:
            self.assertNotIn(other.name, text)
            self.assertNotIn(str(other.id), text)
        self.assertTrue(request.irg_guard_blocked)

    def test_guard_finance_rejects_order_outside_original_company_scope(self):
        request = self.request(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.with_user(self.academic).action_approve_academic()
        foreign = self.env['res.company'].create({'name': 'Guard other company'})
        # SQL represents an external reassignment without triggering unrelated
        # sales company constraints. This write is confined to the test savepoint.
        self.cr.execute('UPDATE sale_order SET company_id=%s WHERE id=%s', (foreign.id, self.sale_order.id))
        self.sale_order.invalidate_recordset()
        with self.assertRaises(AccessError):
            request.with_user(self.accountant).with_context(allowed_company_ids=[self.env.company.id]).action_approve_finance()
        self.assertEqual(request.state, 'academic_approved')

    def test_guard_finance_modality_continuity(self):
        request = self.request(change_modality=True, dest_modality='Homeclass',
                               change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.with_user(self.academic).action_approve_academic()
        self.sale_order.order_line.x_studio_modalidad = 'Presencial'
        request.with_user(self.accountant).action_approve_finance()
        self.assertEqual(self.sale_order.payment_mode_id, self.pay_origin)
        self.assertEqual(self.sale_order.order_line.x_studio_modalidad, 'Presencial')
        self.assertTrue(request.irg_guard_blocked)

    def test_guard_finance_modality_success(self):
        self.sale_order.order_line.copy({'order_id': self.sale_order.id, 'x_studio_modalidad': 'Presencial'})
        request = self.request(change_modality=True, dest_modality='Homeclass',
                               change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        request.with_user(self.academic).action_approve_academic()
        request.with_user(self.accountant).action_approve_finance()
        self.assertEqual(self.sale_order.payment_mode_id, self.pay_dest)
        self.assertEqual(set(self.sale_order.order_line.mapped('x_studio_modalidad')), {'Homeclass'})
        self.assertEqual(request.finance_user_id, self.accountant)

    def test_guard_copy_requires_fresh_request(self):
        request = self.request()
        with self.assertRaises(AccessError):
            request.copy()

    def test_guard_fallback_order_identity_is_verified(self):
        self.sale_order.student_id = False
        request = self.request(change_payment=True, dest_payment_mode_id=self.pay_dest.id)
        self.sale_order.partner_id = self.env['res.partner'].create({'name': 'Different recipient'})
        request.action_approve_academic()
        self.assertEqual(request.state, 'submitted')
        self.assertTrue(request.irg_guard_blocked)


    def test_guard_request_defaults_cannot_inject_changes(self):
        # RPC defaults must not add a payment change omitted from explicit vals.
        request = self.env['irg.enrollment.change'].with_context(
            default_change_payment=True,
            default_sale_order_id=self.sale_order.id,
            default_dest_payment_mode_id=self.pay_dest.id,
        ).create({
            'student_id': self.student.id,
            'student_course_id': self.student_course.id,
            'change_batch': True,
            'dest_batch_id': self.batch_dest.id,
        })
        self.assertFalse(request.change_payment)
        self.assertFalse(request.sale_order_id)
        self.assertFalse(request.dest_payment_mode_id)
        request.action_approve_academic()
        self.assertEqual(request.state, 'done')
        self.assertEqual(self.sale_order.payment_mode_id, self.pay_origin)

    def test_guard_saved_defaults_cannot_supply_protected_values(self):
        Default = self.env['ir.default']
        Default.set('irg.enrollment.change', 'academic_user_id', self.env.uid)
        Default.set('irg.enrollment.change', 'change_payment', True)
        Default.set('irg.enrollment.change', 'dest_payment_mode_id', self.pay_dest.id)
        request = self.direct()
        self.assertFalse(request.academic_user_id)
        self.assertFalse(request.change_payment)
        self.assertFalse(request.dest_payment_mode_id)
