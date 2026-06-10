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
            'course_type': 'online',
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

    def test_bonificado_recurring_order_without_recurrence_confirms(self):
        from dateutil.relativedelta import relativedelta
        from odoo import fields
        # Create a sale order with a recurring product, price_unit = 0, and no recurrence_id
        bonificado_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'course_id': self.course.id,
            'admission_date': fields.Date.today() + relativedelta(months=6),
            'recurrence_id': False,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 0.0,
            })],
        })
        # Confirming the order transitions the state and triggers the constraint
        bonificado_order.action_confirm()
        self.assertIn(bonificado_order.state, ['sale', 'done'])

    def test_discount_line_ignored_by_academic_lines(self):
        # Create a discount product named 'Dcto. Diplomado' with a negative price
        discount_category = self.env['product.category'].create({
            'name': 'Descuentos',
            'code': 'DESC',
        })
        discount_tmpl = self.env['product.template'].create({
            'name': 'Dcto. Diplomado',
            'is_academic_program': True,
            'recurring_invoice': False,
            'categ_id': discount_category.id,
            'list_price': -100.0,
        })
        discount_product = self.env['product.product'].search([
            ('product_tmpl_id', '=', discount_tmpl.id),
        ], limit=1)

        # Create a sale order with an academic product (positive price) and the discount line (negative price)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'course_id': self.course.id,
            'admission_date': date(2026, 6, 28),
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 1000.0,
                }),
                (0, 0, {
                    'product_id': discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -100.0,
                })
            ],
        })

        discount_line = order.order_line.filtered(lambda l: l.product_id == discount_product)
        academic_line = order.order_line.filtered(lambda l: l.product_id == self.product)

        # Assert that the discount line is ignored by _is_academic_line
        self.assertFalse(order._is_academic_line(discount_line))
        # Assert that the academic line is NOT ignored
        self.assertTrue(order._is_academic_line(academic_line))

        # Check wizard logic
        wizard = self.env['irg.manual.confirmation.wizard'].create({
            'order_id': order.id,
            'admission_date': date(2026, 6, 28),
        })
        # Assert that the wizard ignores the discount line in its _is_academic_line check
        self.assertFalse(wizard._is_academic_line(discount_line))
        self.assertTrue(wizard._is_academic_line(academic_line))

    def test_discount_zero_total_order_confirms(self):
        from odoo import fields
        from dateutil.relativedelta import relativedelta

        discount_category = self.env['product.category'].create({
            'name': 'Descuentos',
            'code': 'DESC',
        })
        discount_tmpl = self.env['product.template'].create({
            'name': 'Descuento 100%',
            'is_academic_program': False,
            'recurring_invoice': False,
            'categ_id': discount_category.id,
            'list_price': -1000.0,
            'course_type': 'none',
        })
        discount_product = self.env['product.product'].search([
            ('product_tmpl_id', '=', discount_tmpl.id),
        ], limit=1)

        # Create a sale order with one positive recurring line (1000 €) and one negative discount line (-1000 €) without recurrence_id
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'course_id': self.course.id,
            'admission_date': fields.Date.today() + relativedelta(months=6),
            'recurrence_id': False,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 1000.0,
                }),
                (0, 0, {
                    'product_id': discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -1000.0,
                })
            ],
        })

        # Confirm the order
        order.action_confirm()

        # Verify it confirms successfully
        self.assertIn(order.state, ['sale', 'done'])

        # Verify no payment schedules are created
        self.assertEqual(len(order.subscription_schedule), 0)

