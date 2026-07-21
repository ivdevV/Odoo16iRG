# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase


class TestPartnerGender(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Partner = self.env['res.partner']
        self.SaleOrder = self.env['sale.order']

        self.product = self.env['product.product'].create({
            'name': 'IRG Gender Product',
            'type': 'service',
        })
        self.course = self.env['op.course'].create({
            'name': 'IRG Gender Course',
            'code': 'IRG-GEN-C',
        })
        if 'product_template_id' in self.course._fields:
            self.course.product_template_id = self.product.product_tmpl_id.id
        self.register = self.env['op.admission.register'].create({
            'name': 'IRG Gender Register',
            'course_id': self.course.id,
            'period': '2026-07',
            'start_date': '2026-07-01',
            'end_date': '2026-07-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })
        self.batch = self.env['op.batch'].create({
            'name': 'IRG Gender Batch',
            'code': 'IRG-GEN-B',
            'course_id': self.course.id,
            'start_date': '2026-07-01',
            'end_date': '2026-12-31',
        })
        self.fees_term = self.env['op.fees.terms'].search([], limit=1)
        if not self.fees_term:
            self.fees_term = self.env['op.fees.terms'].create({
                'name': 'IRG Gender Fees',
                'fees_terms': 'fixed_days',
            })

    def test_01_resolve_prefers_order_gender(self):
        partner = self.Partner.create({
            'name': 'Maria Lopez',
            'gender': 'f',
        })
        order = self.SaleOrder.new({
            'partner_id': partner.id,
            'gender': 'm',
        })
        self.assertEqual(order._irg_resolve_admission_gender(partner), 'm')
        self.assertEqual(partner.gender, 'f')

    def test_02_resolve_uses_partner_gender(self):
        partner = self.Partner.create({
            'name': 'Unknown Name',
            'gender': 'female',
        })
        order = self.SaleOrder.new({
            'partner_id': partner.id,
        })
        self.assertEqual(order._irg_resolve_admission_gender(partner), 'f')

    def test_03_resolve_guesses_and_writes_back(self):
        partner = self.Partner.create({
            'name': 'Maria Garcia',
        })
        self.assertFalse(partner.gender)
        order = self.SaleOrder.new({
            'partner_id': partner.id,
        })
        self.assertEqual(order._irg_resolve_admission_gender(partner), 'f')
        self.assertEqual(partner.gender, 'f')

    def test_04_resolve_fallback_other(self):
        partner = self.Partner.create({
            'name': 'Xyzqwl Abc',
        })
        order = self.SaleOrder.new({
            'partner_id': partner.id,
        })
        self.assertEqual(order._irg_resolve_admission_gender(partner), 'o')

    def test_05_admission_create_after_resolve_uses_partner_gender(self):
        """Mirrors SO admission vals: resolve first, then gender from order/partner."""
        partner = self.Partner.create({
            'name': 'Laura Perez',
            'email': 'laura.gender@example.com',
        })
        order = self.SaleOrder.create({
            'partner_id': partner.id,
            'admission_date': fields.Date.today(),
        })
        order._irg_resolve_admission_gender()
        self.assertEqual(partner.gender, 'f')
        admission = self.env['op.admission'].create({
            'name': partner.name,
            'first_name': 'Laura',
            'last_name': 'Perez',
            'partner_id': partner.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
            'gender': order.gender or partner.gender or 'o',
        })
        self.assertEqual(admission.gender, 'f')
