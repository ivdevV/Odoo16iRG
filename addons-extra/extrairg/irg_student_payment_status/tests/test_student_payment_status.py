# -*- coding: utf-8 -*-

from datetime import timedelta
from html import unescape

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tools.misc import format_amount


class TestStudentPaymentStatus(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = cls.env['ir.config_parameter'].sudo()
        cls.param_keys = (
            'irg_student_payment.moroso_threshold',
            'irg_student_payment.grace_days',
            'irg_student_payment.activity_user_id',
        )
        cls.original_params = {
            key: cls.params.get_param(key) for key in cls.param_keys
        }
        cls.params.set_param('irg_student_payment.moroso_threshold', '2')
        cls.params.set_param('irg_student_payment.grace_days', '15')

        cls.income_account = cls.env['account.account'].create({
            'name': 'Test Income IRG Payment Status',
            'code': 'TSTIPST',
            'account_type': 'income',
            'company_id': cls.env.company.id,
        })
        cls.receivable_account = cls.env['account.account'].create({
            'name': 'Test Receivable IRG Payment Status',
            'code': 'TSTRPST',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'company_id': cls.env.company.id,
        })
        cls.sale_journal = cls.env['account.journal'].create({
            'name': 'Test Sales IRG Payment Status',
            'code': 'TSPST',
            'type': 'sale',
            'company_id': cls.env.company.id,
            'default_account_id': cls.income_account.id,
        })
        cls.bank_account = cls.env['account.account'].create({
            'name': 'Test Bank IRG Payment Status',
            'code': 'TSTBPST',
            'account_type': 'asset_cash',
            'company_id': cls.env.company.id,
        })
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Test Bank IRG Payment Status',
            'code': 'TBPST',
            'type': 'bank',
            'company_id': cls.env.company.id,
            'default_account_id': cls.bank_account.id,
        })
        cls.bank_journal.inbound_payment_method_line_ids.write({
            'payment_account_id': cls.bank_account.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Course IRG Payment Status',
            'type': 'service',
            'property_account_income_id': cls.income_account.id,
        })
        cls.manager = cls.env.ref('base.user_admin')
        cls.manager.write({
            'groups_id': [(4, cls.env.ref(
                'openeducat_core.group_op_back_office_admin'
            ).id)]
        })
        cls.params.set_param(
            'irg_student_payment.activity_user_id', str(cls.manager.id)
        )

    @classmethod
    def tearDownClass(cls):
        for key, value in cls.original_params.items():
            if value is False:
                cls.params.search([('key', '=', key)]).unlink()
            else:
                cls.params.set_param(key, value)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.params.set_param('irg_student_payment.moroso_threshold', '2')
        self.params.set_param('irg_student_payment.grace_days', '15')
        self.params.set_param(
            'irg_student_payment.activity_user_id', str(self.manager.id)
        )
        partner = self.env['res.partner'].create({
            'name': 'Student IRG Payment Status',
            'email': 'student.payment.status@example.com',
            'property_account_receivable_id': self.receivable_account.id,
        })
        self.student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Student',
            'last_name': 'Payment Status',
            'gender': 'm',
            'birth_date': '2000-01-01',
        })

    def _create_invoice(self, days_overdue=30, move_type='out_invoice',
                        partner=None, amount=100.0, student_partner=None,
                        currency=None):
        partner = partner or self.student.partner_id
        partner.property_account_receivable_id = self.receivable_account.id
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'journal_id': self.sale_journal.id,
            'currency_id': (currency or self.env.company.currency_id).id,
            'invoice_date': fields.Date.today() - timedelta(days=days_overdue + 1),
            'invoice_date_due': fields.Date.today() - timedelta(days=days_overdue),
            'invoice_line_ids': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'account_id': self.income_account.id,
                'quantity': 1.0,
                'price_unit': amount,
            })],
        })
        invoice.action_post()
        if student_partner:
            self.env.cr.execute(
                'UPDATE account_move SET irg_student_partner_id = %s WHERE id = %s',
                [student_partner.id, invoice.id],
            )
            invoice.invalidate_recordset(['irg_student_partner_id'])
        return invoice

    def _create_academic_user(self, login='academic.payment.reader@example.com'):
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Academic Payment Reader',
            'login': login,
            'email': login,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('openeducat_core.group_op_faculty').id,
            ])],
        })

    def _default_activities(self):
        todo = self.env.ref('mail.mail_activity_data_todo')
        return self.student.activity_ids.filtered(
            lambda activity: (
                activity.activity_type_id == todo
                and activity.summary == 'Seguimiento de morosidad'
            )
        )

    def _pay_invoice(self, invoice):
        register = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids
        ).create({
            'journal_id': self.bank_journal.id,
            'payment_date': fields.Date.today(),
        })
        register.action_create_payments()
        invoice.invalidate_recordset()

    def test_no_invoices_is_up_to_date(self):
        self.assertEqual(self.student._irg_compute_payment_status(), 'al_dia')
        self.assertEqual(self.student.irg_overdue_invoice_count, 0)
        self.assertEqual(self.student.irg_overdue_amount, 0.0)

    def test_one_invoice_outside_grace_is_late(self):
        self._create_invoice(days_overdue=16)

        self.assertEqual(self.student._irg_compute_payment_status(), 'atrasado')
        self.assertEqual(self.student.irg_overdue_invoice_count, 1)
        self.assertEqual(self.student.irg_overdue_amount, 100.0)

    def test_threshold_enters_default_and_creates_one_activity(self):
        self._create_invoice(days_overdue=30)
        self._create_invoice(days_overdue=20)

        student = self.student.with_user(self.manager)
        student.action_irg_update_payment_status()
        student.action_irg_update_payment_status()

        self.assertEqual(self.student.irg_payment_status, 'moroso')
        activities = self._default_activities()
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.activity_type_id, self.env.ref(
            'mail.mail_activity_data_todo'
        ))
        self.assertEqual(activities.user_id, self.manager)
        bodies = self.student.message_ids.mapped('body')
        transition_body = next(
            body for body in bodies
            if 'Estado de pago actualizado' in body
        )
        self.assertIn('Al día → Moroso', transition_body)
        self.assertIn('Facturas vencidas: 2', transition_body)
        self.assertIn('200', transition_body)
        self.assertIn('Gracia aplicada: 15 días', transition_body)
        self.assertIn(self.env.company.currency_id.symbol, transition_body)

    def test_invoice_inside_grace_does_not_count(self):
        self._create_invoice(days_overdue=15)

        self.assertEqual(self.student._irg_compute_payment_status(), 'al_dia')
        self.assertEqual(self.student.irg_overdue_invoice_count, 0)

    def test_cron_returns_paid_debt_from_default_to_up_to_date(self):
        invoices = self._create_invoice(30) | self._create_invoice(20)
        self.env['op.student']._cron_update_payment_status()
        for invoice in invoices:
            self._pay_invoice(invoice)

        self.env['op.student']._cron_update_payment_status()

        self.assertEqual(self.student.irg_payment_status, 'al_dia')
        self.assertTrue(any(
            'regularizada' in body.lower()
            for body in self.student.message_ids.mapped('body')
        ))

    def test_regularization_closes_activity_and_reincidence_creates_new_one(self):
        invoices = self._create_invoice(30) | self._create_invoice(20)
        self.env['op.student']._cron_update_payment_status()
        original_activity = self._default_activities()
        self.assertEqual(len(original_activity), 1)

        for invoice in invoices:
            self._pay_invoice(invoice)
        self.env['op.student']._cron_update_payment_status()

        self.assertFalse(original_activity.exists())
        self.assertFalse(self._default_activities())
        self.assertTrue(any(
            'Seguimiento de morosidad cerrado' in body
            for body in self.student.message_ids.mapped('body')
        ))

        self._create_invoice(40)
        self._create_invoice(30)
        self.env['op.student']._cron_update_payment_status()
        reincidence_activity = self._default_activities()
        self.assertEqual(len(reincidence_activity), 1)
        self.assertNotEqual(reincidence_activity.id, original_activity.id)

        self.env['op.student']._cron_update_payment_status()
        self.assertEqual(len(self._default_activities()), 1)

    def test_foreign_currency_residual_uses_company_currency(self):
        foreign_currency = self.env['res.currency'].create({
            'name': 'XPS',
            'symbol': 'XPS',
            'rounding': 0.01,
            'rate_ids': [(0, 0, {
                'name': fields.Date.today(),
                'rate': 2.0,
                'company_id': self.env.company.id,
            })],
        })
        invoice = self._create_invoice(
            days_overdue=30,
            amount=100.0,
            currency=foreign_currency,
        )
        expected_amount = invoice.amount_residual_signed
        self.assertNotEqual(expected_amount, invoice.amount_residual)

        self.student.with_user(self.manager).action_irg_update_payment_status()

        self.assertEqual(self.student.irg_overdue_amount, expected_amount)
        self.assertEqual(
            self.student.irg_payment_currency_id,
            self.env.company.currency_id,
        )
        expected_display = format_amount(
            self.env, expected_amount, self.env.company.currency_id
        )
        transition_body = next(
            body for body in self.student.message_ids.mapped('body')
            if 'Estado de pago actualizado' in body
        )
        self.assertIn(expected_display, unescape(str(transition_body)))
        self.assertIn(self.env.company.currency_id.symbol, transition_body)

    def test_manual_action_requires_back_office_group_before_changing_status(self):
        self._create_invoice(30)
        academic_user = self._create_academic_user(
            'academic.payment.denied@example.com'
        )
        message_count = len(self.student.message_ids)

        with self.assertRaises(AccessError):
            self.student.with_user(
                academic_user
            ).action_irg_update_payment_status()

        self.assertEqual(self.student.irg_payment_status, 'al_dia')
        self.assertFalse(self.student.irg_payment_status_date)
        self.assertEqual(len(self.student.message_ids), message_count)
        self.assertFalse(self._default_activities())

    def test_manual_action_allows_back_office_user_with_write_access(self):
        self._create_invoice(30)

        self.student.with_user(self.manager).action_irg_update_payment_status()

        self.assertEqual(self.student.irg_payment_status, 'atrasado')
        self.assertEqual(self.student.irg_payment_status_date, fields.Date.today())

    def test_manual_action_respects_write_record_rules(self):
        self._create_invoice(30)
        self.env['ir.rule'].sudo().create({
            'name': 'Deny student payment status write in test',
            'model_id': self.env['ir.model']._get_id('op.student'),
            'domain_force': "[('id', '=', 0)]",
            'perm_read': False,
            'perm_write': True,
            'perm_create': False,
            'perm_unlink': False,
        })

        with self.assertRaises(AccessError):
            self.student.with_user(self.manager).action_irg_update_payment_status()

        self.assertEqual(self.student.irg_payment_status, 'al_dia')

    def test_third_party_payer_invoice_counts(self):
        payer = self.env['res.partner'].create({
            'name': 'Third Party Payer IRG',
            'property_account_receivable_id': self.receivable_account.id,
        })
        self._create_invoice(
            days_overdue=30,
            partner=payer,
            student_partner=self.student.partner_id,
        )

        self.assertEqual(self.student.irg_overdue_invoice_count, 1)

    def test_refund_does_not_count(self):
        self._create_invoice(days_overdue=30, move_type='out_refund')

        self.assertEqual(self.student.irg_overdue_invoice_count, 0)

    def test_configured_threshold_three_is_respected(self):
        self.params.set_param('irg_student_payment.moroso_threshold', '3')
        self._create_invoice(40)
        self._create_invoice(30)

        self.assertEqual(self.student._irg_compute_payment_status(), 'atrasado')
        self._create_invoice(20)
        self.assertEqual(self.student._irg_compute_payment_status(), 'moroso')

    def test_invalid_parameters_use_safe_fallbacks(self):
        self.params.set_param('irg_student_payment.moroso_threshold', '-3')
        self.params.set_param('irg_student_payment.grace_days', 'invalid')
        self._create_invoice(16)

        self.assertGreaterEqual(self.student._irg_get_moroso_threshold(), 1)
        self.assertGreaterEqual(self.student._irg_get_grace_days(), 0)
        self.assertEqual(self.student._irg_compute_payment_status(), 'atrasado')

    def test_academic_user_can_read_live_computes_without_account_access(self):
        self._create_invoice(30)
        academic_user = self._create_academic_user()

        student = self.student.with_user(academic_user)
        self.assertEqual(student.irg_overdue_invoice_count, 1)
        self.assertEqual(student.irg_overdue_amount, 100.0)
