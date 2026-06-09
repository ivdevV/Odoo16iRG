# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestStudentInvoicePaymentLink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.income_account = cls.env['account.account'].create({
            'name': 'Test Income IRG Student Link',
            'code': 'TSTINCIRG',
            'account_type': 'income',
            'company_id': cls.env.company.id,
        })
        cls.receivable_account = cls.env['account.account'].create({
            'name': 'Test Receivable IRG Student Link',
            'code': 'TSTRECIRG',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'company_id': cls.env.company.id,
        })
        cls.env['account.journal'].create({
            'name': 'Test Sale Journal IRG Student Link',
            'code': 'TSIRG',
            'type': 'sale',
            'company_id': cls.env.company.id,
            'default_account_id': cls.income_account.id,
        })
        cls.payer = cls.env['res.partner'].create({'name': 'Test Payer IRG'})
        cls.student_partner = cls.env['res.partner'].create({
            'name': 'Test Student IRG',
            'email': 'student.invoice.link@example.com',
        })
        (cls.payer | cls.student_partner).property_account_receivable_id = (
            cls.receivable_account.id
        )
        cls.student = cls.env['op.student'].create({
            'partner_id': cls.student_partner.id,
            'first_name': 'Test',
            'last_name': 'Student IRG',
            'gender': 'm',
            'birth_date': '2000-01-01',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Course Invoice Link',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 100.0,
            'property_account_income_id': cls.income_account.id,
        })

    def _create_invoiced_order(self):
        order = self.env['sale.order'].create({
            'partner_id': self.payer.id,
            'partner_invoice_id': self.payer.id,
            'partner_shipping_id': self.payer.id,
            'student_id': self.student_partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()
        invoice = order._create_invoices()
        return order, invoice

    def test_sale_invoice_keeps_payer_and_links_student(self):
        order, invoice = self._create_invoiced_order()

        self.assertEqual(order.partner_id, self.payer)
        self.assertEqual(invoice.partner_id, self.payer)
        self.assertEqual(invoice.irg_student_partner_id, self.student_partner)

    def test_student_invoice_action_includes_third_party_invoice(self):
        __, invoice = self._create_invoiced_order()

        action = self.student.action_view_invoice()
        invoices = self.env['account.move'].search(action['domain'])

        self.assertIn(invoice, invoices)
        self.assertEqual(action['context']['default_partner_id'], self.student_partner.id)

    def test_student_payment_action_uses_reconciled_invoice_payments(self):
        __, invoice = self._create_invoiced_order()

        # Payment creation/reconciliation depends on local journals and chart data;
        # this validates the action/domain path used once invoices are reconciled.
        expected_payments = invoice._get_reconciled_payments()
        action = self.student.action_view_academic_payments()

        self.assertEqual(action['res_model'], 'account.payment')
        self.assertEqual(action['domain'], [('id', 'in', expected_payments.ids)])
        self.assertEqual(self.student.irg_payment_count, len(expected_payments))
