# -*- coding: utf-8 -*-
from datetime import date

from odoo.tests.common import TransactionCase


class TestDiplomadoFixedBatchPeriod(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Diplomado Test Partner'})
        self.category = self.env['product.category'].create({
            'name': 'Diplomados Test Category',
            'code': 'DI',
        })
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Diplomado en Neuroeducacion',
            'is_academic_program': True,
            'recurring_invoice': True,
            'categ_id': self.category.id,
            'list_price': 1000.0,
        })
        self.product = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_tmpl.id),
        ], limit=1)
        self.course = self.env['op.course'].create({
            'name': 'Diplomado en Neuroeducacion',
            'code': 'NE',
            'product_template_id': self.product_tmpl.id,
        })
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'course_id': self.course.id,
            'admission_date': date(2026, 6, 28),
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 1000.0,
            })],
        })
        self.line = self.order.order_line[:1]

    def test_wizard_preview_uses_diplomado_fixed_annual_batch(self):
        wizard = self.env['irg.manual.confirmation.wizard'].create({
            'order_id': self.order.id,
            'admission_date': date(2026, 6, 28),
        })

        self.assertEqual(wizard.modalidad_detected, 'Diplomado')
        self.assertIn('DINEHC2606', wizard.batch_preview)
        self.assertNotIn('dia', wizard.warning_message or '')

    def test_get_lot_id_creates_fixed_diplomado_period(self):
        batch = self.order.with_context(irg_get_lot_line_id=self.line.id).get_lot_id(self.course)

        self.assertEqual(self.order._get_line_modality(self.line), 'GE')
        self.assertEqual(batch.code, 'DINEHC2606')
        self.assertEqual(batch.start_date, date(2026, 6, 28))
        self.assertEqual(batch.end_date, date(2026, 9, 30))
        self.assertEqual(batch.date_start_class, date(2026, 6, 28))

    def test_non_diplomado_master_delegates_to_existing_logic(self):
        master_category = self.env['product.category'].create({
            'name': 'Master Test Category',
            'code': 'M',
        })
        master_tmpl = self.env['product.template'].create({
            'name': 'Master HC Test',
            'is_academic_program': True,
            'recurring_invoice': True,
            'categ_id': master_category.id,
            'list_price': 2000.0,
        })
        master_product = self.env['product.product'].search([
            ('product_tmpl_id', '=', master_tmpl.id),
        ], limit=1)
        master_course = self.env['op.course'].create({
            'name': 'Master HC Test',
            'code': 'MH',
            'product_template_id': master_tmpl.id,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'course_id': master_course.id,
            'admission_date': date(2026, 6, 28),
            'order_line': [(0, 0, {
                'product_id': master_product.id,
                'product_uom_qty': 1,
                'price_unit': 2000.0,
            })],
        })

        wizard = self.env['irg.manual.confirmation.wizard'].create({
            'order_id': order.id,
            'admission_date': date(2026, 6, 28),
        })

        self.assertNotEqual(wizard.modalidad_detected, 'Diplomado')
        self.assertNotIn('DIMHHC2606', wizard.batch_preview)

    def test_header_diplomado_course_does_not_contaminate_other_line(self):
        other_category = self.env['product.category'].create({
            'name': 'Other Academic Category',
            'code': 'M',
        })
        other_tmpl = self.env['product.template'].create({
            'name': 'Master Compartido Test',
            'is_academic_program': True,
            'recurring_invoice': True,
            'categ_id': other_category.id,
            'list_price': 2000.0,
        })
        other_product = self.env['product.product'].search([
            ('product_tmpl_id', '=', other_tmpl.id),
        ], limit=1)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'course_id': self.course.id,
            'admission_date': date(2026, 6, 28),
            'order_line': [(0, 0, {
                'product_id': other_product.id,
                'product_uom_qty': 1,
                'price_unit': 2000.0,
            })],
        })
        line = order.order_line[:1]

        self.assertFalse(order._irg_is_diplomado_line(line, order.course_id))
