# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase
from odoo import fields

_logger = logging.getLogger(__name__)


class TestRegisterDateValidation(TransactionCase):

    def setUp(self):
        super(TestRegisterDateValidation, self).setUp()

        # Create a product template
        self.product_template = self.env['product.template'].create({
            'name': 'Test Academic Program Product',
            'type': 'service',
            'is_academic_program': True,
            'recurring_invoice': True,
        })

        # Create a course linked to the product template
        self.course = self.env['op.course'].create({
            'name': 'Test Course for Date Validation',
            'code': 'T-CDV-01',
            'product_template_id': self.product_template.id,
        })

        # Create a dummy sale order to invoke the method on
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.partner_admin').id,
        })

    def test_search_matches_alternative_period_format(self):
        """Test that the robust search logic matches existing registers even when period formatting differs (e.g. '2026-02' vs '2026-2')."""
        # Create an admission register using the standard length-7 format ('2026-02') to bypass initial Odoo validations
        register = self.env['op.admission.register'].create({
            'name': 'Test Register 2026-2',
            'course_id': self.course.id,
            'period': '2026-02',
            'start_date': '2026-02-01',
            'end_date': '2026-05-31',
            'min_count': 1,
            'max_count': 500,
        })

        # Force state to confirm
        register.write({'state': 'confirm'})

        # Bypass the Odoo validation constraint via direct SQL to change the period to '2026-2'
        self.env.cr.execute(
            "UPDATE op_admission_register SET period = '2026-2' WHERE id = %s",
            [register.id]
        )
        register.invalidate_recordset(['period'])

        # Check search with '2026-02' finds the register which has period '2026-2'
        res_register = self.sale_order._find_or_create_register(
            period='2026-02',
            product_template=self.product_template,
            course=self.course
        )
        self.assertEqual(res_register, register)
        self.assertEqual(res_register.state, 'application')

        # Test the converse: existing register is '2026-02' and we search with '2026-2'
        # Set state back to confirm for testing
        register.write({'state': 'confirm'})
        self.env.cr.execute(
            "UPDATE op_admission_register SET period = '2026-02' WHERE id = %s",
            [register.id]
        )
        register.invalidate_recordset(['period'])

        res_register_alt = self.sale_order._find_or_create_register(
            period='2026-2',
            product_template=self.product_template,
            course=self.course
        )
        self.assertEqual(res_register_alt, register)
        self.assertEqual(res_register_alt.state, 'application')

    def test_date_safeguard_for_past_periods(self):
        """Test that creating a register for a past period (where the end_date is in the past)
        does not crash and sets the start_date and end_date to the period's end_date.
        """
        past_period = '2025-02'
        expected_end_date = self.sale_order.gat_date_max_register(past_period)

        # Clear any existing registers for the past period to ensure we trigger creation
        existing = self.env['op.admission.register'].search([
            ('course_id', '=', self.course.id),
            ('period', '=', past_period)
        ])
        if existing:
            existing.unlink()

        # Call _find_or_create_register which should pre-create the register using the safeguard logic
        res_register = self.sale_order._find_or_create_register(
            period=past_period,
            product_template=self.product_template,
            course=self.course
        )

        self.assertEqual(res_register.period, past_period)
        self.assertEqual(res_register.start_date, expected_end_date)
        self.assertEqual(res_register.end_date, expected_end_date)
        self.assertEqual(res_register.state, 'application')

    def test_wizard_shows_detected_register_name(self):
        """Test that the wizard's detected_registers_preview field details the matched register's name
        or indicates that a new one will be created.
        """
        # Create a sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.partner_admin').id,
        })

        # Get or create the product variant for our academic product template
        product = self.product_template.product_variant_id or self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_template.id)
        ], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'product_tmpl_id': self.product_template.id,
            })

        # Create order line
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': product.id,
            'name': product.name,
            'price_unit': 100.0,
            'product_uom_qty': 1.0,
        })

        # Create wizard with an admission date
        wizard = self.env['irg.manual.confirmation.wizard'].create({
            'order_id': sale_order.id,
            'admission_date': fields.Date.to_date('2026-02-01'),
        })

        # Calculate period fallback: month=2 -> period='2026-01'
        # Check that it initially indicates a new one will be created
        wizard._compute_preview()
        expected_no_register = f"{self.product_template.name}: (Se creará un nuevo registro)"
        self.assertEqual(wizard.detected_registers_preview, expected_no_register)

        # Now create the matching register
        register = self.env['op.admission.register'].create({
            'name': 'Matching Register 2026-01',
            'course_id': self.course.id,
            'period': '2026-01',
            'start_date': '2026-01-01',
            'end_date': '2026-03-31',
            'min_count': 1,
            'max_count': 500,
        })
        register.write({'state': 'application'})

        # Re-compute preview and check that it details the matched register's name
        wizard._compute_preview()
        expected_with_register = f"{self.product_template.name}: Matching Register 2026-01"
        self.assertEqual(wizard.detected_registers_preview, expected_with_register)
