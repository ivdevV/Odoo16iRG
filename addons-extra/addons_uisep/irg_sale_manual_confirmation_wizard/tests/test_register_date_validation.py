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
            'course_type': 'classroom',
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

    def test_es_ES_academic_confirmation_routing(self):
        """Test that confirming a sale order with an academic product and course lang 'es_ES':
        - Natively (without wizard context) creates the admission but does NOT auto-enroll it (state is draft/application, email_send_ok is False).
        - With wizard context (irg_manual_wizard_passed=True) forces full enrollment (state is done, email_send_ok is True).
        """
        # Ensure es_ES lang exists and is active
        lang_code = 'es_ES'
        lang = self.env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)])
        if lang:
            if not lang.active:
                lang.write({'active': True})
        else:
            self.env['res.lang'].create({
                'name': 'Spanish (ES)',
                'code': lang_code,
                'iso_code': 'es',
                'direction': 'ltr',
            })

        # Set course language to es_ES
        self.course.write({'lang': lang_code})

        # Ensure we have at least one recurrence plan for the sale orders
        recurrence = self.env['sale.temporal.recurrence'].search([], limit=1)
        if not recurrence:
            recurrence = self.env['sale.temporal.recurrence'].create({
                'duration': 1,
                'unit': 'month',
            })

        # Ensure we have at least one fees term
        if not self.env['op.fees.terms'].search([], limit=1):
            self.env['op.fees.terms'].create({'name': 'Test Fees Term'})

        # Ensure auto.admission.required exists and is configured
        ad = self.env['auto.admission.required'].search([], limit=1)
        if not ad:
            self.env['auto.admission.required'].create({
                'manual_wizard_enabled': True,
                'mx_active': True,
                'mx_state_admission_done': True,
                'mx_auto_email_welcome': True,
            })
        else:
            ad.write({
                'manual_wizard_enabled': True,
                'mx_active': True,
                'mx_state_admission_done': True,
                'mx_auto_email_welcome': True,
            })

        # Ensure the mail template exists to prevent ref lookup error
        xml_id = 'isep_elearning_custom.email_op_admission_confirm'
        try:
            self.env.ref(xml_id)
        except ValueError:
            admission_model = self.env['ir.model'].search([('model', '=', 'op.admission')], limit=1)
            template = self.env['mail.template'].create({
                'name': 'Test Admission Confirmation Template',
                'model_id': admission_model.id,
                'subject': 'Confirmación de Admisión',
                'body_html': 'Hola ${object.new_password_user}',
            })
            module, name = xml_id.split('.')
            self.env['ir.model.data'].create({
                'name': name,
                'module': module,
                'model': 'mail.template',
                'res_id': template.id,
                'noupdate': True,
            })

        # Set email, phone, and recurrence on native sale order
        self.sale_order.write({
            'recurrence_id': recurrence.id,
            'start_date': fields.Date.to_date('2026-02-01'),
            'end_date': fields.Date.to_date('2026-03-01'),
        })
        self.sale_order.partner_id.write({
            'email': 'test_student@example.com',
            'phone': '123456789',
        })

        # Get the product variant
        product = self.product_template.product_variant_id or self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_template.id)
        ], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'product_tmpl_id': self.product_template.id,
            })

        # Add line to native sale order
        self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': product.id,
            'name': product.name,
            'price_unit': 100.0,
            'product_uom_qty': 1.0,
            'start_date_enroller': fields.Date.to_date('2026-02-01'),
        })

        # Pre-create admission registers spanning today to avoid "Application Date should be between Start Date & End Date" error.
        from datetime import timedelta
        today = fields.Date.today()
        for p in ['2026-01', '2026-02']:
            reg = self.env['op.admission.register'].create({
                'name': f'Pre-created Register {p}',
                'course_id': self.course.id,
                'period': p,
                'start_date': today - timedelta(days=10),
                'end_date': today + timedelta(days=30),
                'min_count': 1,
                'max_count': 500,
                'product_template_id': self.product_template.id,
            })
            reg.write({'state': 'application'})

        # Case A: Confirm native sale order (without manual wizard context)
        self.sale_order.action_confirm()

        # Check native admission
        native_admission = self.env['op.admission'].search([('sale_id', '=', self.sale_order.id)])
        self.assertTrue(native_admission, "An admission should have been created natively")
        self.assertIn(native_admission.state, ['draft', 'application'], "The native admission state must not be promoted to 'done'")
        self.assertFalse(native_admission.email_send_ok, "The native admission email_send_ok must be False")

        # Case B: Confirm wizard sale order (with irg_manual_wizard_passed = True)
        sale_order_wizard = self.env['sale.order'].create({
            'partner_id': self.sale_order.partner_id.id,
            'recurrence_id': recurrence.id,
            'start_date': fields.Date.to_date('2026-02-01'),
            'end_date': fields.Date.to_date('2026-03-01'),
        })
        self.env['sale.order.line'].create({
            'order_id': sale_order_wizard.id,
            'product_id': product.id,
            'name': product.name,
            'price_unit': 100.0,
            'product_uom_qty': 1.0,
            'start_date_enroller': fields.Date.to_date('2026-02-01'),
        })

        sale_order_wizard.with_context(irg_manual_wizard_passed=True).action_confirm()

        # Check wizard admission
        wizard_admission = self.env['op.admission'].search([('sale_id', '=', sale_order_wizard.id)])
        self.assertTrue(wizard_admission, "An admission should have been created via the wizard context")
        self.assertEqual(wizard_admission.state, 'done', "The wizard admission state must be 'done'")
        self.assertTrue(wizard_admission.email_send_ok, "The wizard admission email_send_ok must be True")

    def test_master_batch_prefix_normalization(self):
        """Test master batch code formatting and prefix normalization logic in get_lot_id:
        - Category code starting with M / name containing 'Master' gets MO (for Oficial) or MP (otherwise).
        - Course code starting with M has the prefix 'M' sliced if the category is master.
        """
        # Create product category with code 'MOM'
        master_category = self.env['product.category'].create({
            'name': 'Master Category',
            'code': 'MOM',
        })

        # Course 1: Máster Oficial en Sexología Clínica (code: MSC_MO)
        course_oficial = self.env['op.course'].create({
            'name': 'Máster Oficial en Sexología Clínica',
            'code': 'MSC_MO',
        })
        pt_oficial = self.env['product.template'].create({
            'name': 'Test Academic Program Product Oficial',
            'type': 'service',
            'is_academic_program': True,
            'recurring_invoice': True,
            'categ_id': master_category.id,
            'course_type': 'classroom',
        })
        course_oficial.write({'product_template_id': pt_oficial.id})

        # Create a dummy sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.partner_admin').id,
        })

        # Test Case A: Oficial Course batch code starts with 'MOSC'
        batch_oficial = sale_order.get_lot_id(course_oficial)
        self.assertTrue(batch_oficial, "Should have created or found the batch for oficial course")
        self.assertTrue(batch_oficial.code.startswith('MOSC'), f"Expected code to start with MOSC, got {batch_oficial.code}")

        # Course 2: Máster en Sexología Clínica (code: MSC_MP)
        course_master = self.env['op.course'].create({
            'name': 'Máster en Sexología Clínica',
            'code': 'MSC_MP',
        })
        pt_master = self.env['product.template'].create({
            'name': 'Test Academic Program Product Master',
            'type': 'service',
            'is_academic_program': True,
            'recurring_invoice': True,
            'categ_id': master_category.id,
            'course_type': 'classroom',
        })
        course_master.write({'product_template_id': pt_master.id})

        # Test Case B: Regular Master Course batch code starts with 'MPSC'
        batch_master = sale_order.get_lot_id(course_master)
        self.assertTrue(batch_master, "Should have created or found the batch for regular master course")
        self.assertTrue(batch_master.code.startswith('MPSC'), f"Expected code to start with MPSC, got {batch_master.code}")

    def test_native_confirmation_es_ES_no_batch_creation(self):
        """Test that native confirmation of a sale order with an es_ES course:
        - Creates the admission in 'draft' or 'application' state.
        - Does NOT create any batch record in the database.
        - The admission batch_id is False.
        """
        # Ensure es_ES lang exists and is active
        lang_code = 'es_ES'
        lang = self.env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)])
        if lang:
            if not lang.active:
                lang.write({'active': True})
        else:
            self.env['res.lang'].create({
                'name': 'Spanish (ES)',
                'code': lang_code,
                'iso_code': 'es',
                'direction': 'ltr',
            })

        # Create a course with code 'SC_ES' and language 'es_ES'
        course = self.env['op.course'].create({
            'name': 'Sexología Clínica España',
            'code': 'SC_ES',
            'lang': lang_code,
        })

        # Create product template and link to course
        product_template = self.env['product.template'].create({
            'name': 'Sexología Clínica Product',
            'type': 'service',
            'is_academic_program': True,
            'recurring_invoice': True,
            'course_type': 'classroom',
        })
        course.write({'product_template_id': product_template.id})

        # Ensure we have a recurrence plan
        recurrence = self.env['sale.temporal.recurrence'].search([], limit=1)
        if not recurrence:
            recurrence = self.env['sale.temporal.recurrence'].create({
                'duration': 1,
                'unit': 'month',
                'name': 'Monthly Recurrence',
            })

        # Create a sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.partner_admin').id,
            'recurrence_id': recurrence.id,
            'start_date': fields.Date.to_date('2026-02-01'),
            'end_date': fields.Date.to_date('2026-03-01'),
        })
        sale_order.partner_id.write({
            'email': 'es_student@example.com',
            'phone': '987654321',
        })

        # Get product variant
        product = product_template.product_variant_id or self.env['product.product'].search([
            ('product_tmpl_id', '=', product_template.id)
        ], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'product_tmpl_id': product_template.id,
            })

        # Add line to sale order
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': product.id,
            'name': product.name,
            'price_unit': 100.0,
            'product_uom_qty': 1.0,
            'start_date_enroller': fields.Date.to_date('2026-02-01'),
        })

        # Pre-create admission register spanning today (period maps to 2026-01 due to month=2)
        from datetime import timedelta
        today = fields.Date.today()
        reg = self.env['op.admission.register'].create({
            'name': 'Pre-created SC Register',
            'course_id': course.id,
            'period': '2026-01',
            'start_date': today - timedelta(days=10),
            'end_date': today + timedelta(days=30),
            'min_count': 1,
            'max_count': 500,
            'product_template_id': product_template.id,
        })
        reg.write({'state': 'application'})

        # Verify no batches exist for this course before confirmation
        batches_before = self.env['op.batch'].search([('course_id', '=', course.id)])
        self.assertEqual(len(batches_before), 0, "No batches should exist for this course initially")

        # Confirm the sale order natively (without context)
        sale_order.action_confirm()

        # Check admission is created in draft/application state
        admission = self.env['op.admission'].search([('sale_id', '=', sale_order.id)])
        self.assertTrue(admission, "An admission should have been created")
        self.assertIn(admission.state, ['draft', 'application'], "The admission state must remain in draft/application")

        # Check that no batch has been created in the database for this course
        batches_after = self.env['op.batch'].search([('course_id', '=', course.id)])
        self.assertEqual(len(batches_after), 0, "No batch should have been created during native confirmation")
        self.assertFalse(admission.batch_id, "The admission batch_id must be empty/False")


