# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields


class TestIntensivoWizardPreview(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Partner = self.env['res.partner']
        self.ProductTemplate = self.env['product.template']
        self.ProductProduct = self.env['product.product']
        self.ProductAttribute = self.env['product.attribute']
        self.ProductAttributeValue = self.env['product.attribute.value']
        self.ProductTemplateAttributeLine = self.env['product.template.attribute.line']
        self.OpCourse = self.env['op.course']
        self.OpModality = self.env['op.modality']
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']
        self.Wizard = self.env['irg.manual.confirmation.wizard']

        self.master_category = self.env['product.category'].create({
            'name': 'Master Oficial Category',
            'code': 'MO',
        })

        self.course_pc = self.OpCourse.create({
            'name': 'Máster Oficial PC',
            'code': 'PC',
            'lang': 'en_US',
        })

        self.attr_modalidad = self.ProductAttribute.create({'name': 'Modalidad'})
        self.val_intensivo = self.ProductAttributeValue.create({
            'name': 'Intensivo',
            'attribute_id': self.attr_modalidad.id,
        })

        # Modality record
        self.modality_in = self.OpModality.search([('code', '=', 'IN')], limit=1)
        if not self.modality_in:
            self.modality_in = self.OpModality.create({
                'name': 'Intensivo',
                'code': 'IN',
                'new_code': 'IN',
            })

        self.product_tmpl = self.ProductTemplate.create({
            'name': 'Programa Máster Oficial PC',
            'type': 'service',
            'is_academic_program': True,
            'categ_id': self.master_category.id,
        })
        self.course_pc.write({'product_template_id': self.product_tmpl.id})

        self.ptal = self.ProductTemplateAttributeLine.create({
            'product_tmpl_id': self.product_tmpl.id,
            'attribute_id': self.attr_modalidad.id,
            'value_ids': [(6, 0, [self.val_intensivo.id])],
        })

        self.product_variant = self.ProductProduct.search([
            ('product_tmpl_id', '=', self.product_tmpl.id),
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.val_intensivo.id)
        ], limit=1)
        if not self.product_variant:
            ptav = self.ptal.product_template_value_ids.filtered(
                lambda v: v.product_attribute_value_id == self.val_intensivo
            )
            self.product_variant = self.ProductProduct.create({
                'product_tmpl_id': self.product_tmpl.id,
                'product_template_attribute_value_ids': [(6, 0, ptav.ids)],
            })

        self.customer = self.Partner.create({
            'name': 'Student Intensivo Wizard',
            'email': 'student_intensivo@example.com',
            'birth_date': '2000-05-15',
        })

    def test_wizard_preview_and_confirm_mopcin2701(self):
        """Test wizard preview detects modality IN, previews MOPCIN2701, and manual confirmation sets irg_is_intensive."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'admission_date': fields.Date.to_date('2027-01-01'),
        })
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product_variant.id,
            'product_uom_qty': 1,
            'price_unit': 1200.0,
            'start_date_enroller': fields.Date.to_date('2027-01-01'),
        })

        wizard = self.Wizard.create({
            'order_id': order.id,
            'admission_date': fields.Date.to_date('2027-01-01'),
        })

        self.assertIn('IN', wizard.modalidad_detected, f"Expected IN modality detected, got {wizard.modalidad_detected}")
        self.assertIn('MOPCIN2701', wizard.batch_preview, f"Expected MOPCIN2701 in batch preview, got {wizard.batch_preview}")

        # Confirm order via wizard
        wizard.action_confirm()

        admission = self.env['op.admission'].search([('order_id', '=', order.id)], limit=1)
        self.assertTrue(admission, "Admission should be created")
        self.assertEqual(admission.batch_id.code, 'MOPCIN2701', f"Expected batch code MOPCIN2701, got {admission.batch_id.code}")
        self.assertTrue(getattr(admission, 'irg_is_intensive', False), "Admission should have irg_is_intensive = True")

    def test_wizard_preview_and_confirm_with_order_tick_is_intensive(self):
        """Test wizard preview detects modality IN when irg_is_intensive tick is checked on sale.order."""
        product_generic = self.ProductProduct.create({
            'name': 'Programa Máster Oficial Genérico Wizard',
            'type': 'service',
            'is_academic_program': True,
            'categ_id': self.master_category.id,
        })

        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'admission_date': fields.Date.to_date('2027-01-01'),
            'irg_is_intensive': True,
        })
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': product_generic.id,
            'product_uom_qty': 1,
            'price_unit': 1200.0,
            'start_date_enroller': fields.Date.to_date('2027-01-01'),
        })

        wizard = self.Wizard.create({
            'order_id': order.id,
            'admission_date': fields.Date.to_date('2027-01-01'),
        })

        self.assertIn('IN', wizard.modalidad_detected, f"Expected IN modality detected from tick, got {wizard.modalidad_detected}")
        self.assertIn('MOPCIN2701', wizard.batch_preview, f"Expected MOPCIN2701 in batch preview, got {wizard.batch_preview}")

        wizard.action_confirm()

        admission = self.env['op.admission'].search([('order_id', '=', order.id)], limit=1)
        self.assertTrue(admission, "Admission should be created")
        self.assertEqual(admission.batch_id.code, 'MOPCIN2701', f"Expected batch code MOPCIN2701, got {admission.batch_id.code}")
        self.assertTrue(getattr(admission, 'irg_is_intensive', False), "Admission should have irg_is_intensive = True")

    def test_wizard_detects_existing_intensivo_register(self):
        """Test that wizard finds an existing admission register with period 2027-01 for PC course."""
        reg = self.env['op.admission.register'].create({
            'name': '2027-01 Máster en Psicología Clínica y de la Salud',
            'course_id': self.course_pc.id,
            'period': '2027-01',
            'state': 'application',
            'start_date': fields.Date.to_date('2026-07-15'),
            'end_date': fields.Date.to_date('2027-03-31'),
        })
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'admission_date': fields.Date.to_date('2026-07-23'),
            'irg_is_intensive': True,
        })
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product_variant.id,
            'product_uom_qty': 1,
            'price_unit': 1200.0,
            'start_date_enroller': fields.Date.to_date('2026-07-23'),
        })

        wizard = self.Wizard.create({
            'order_id': order.id,
            'admission_date': fields.Date.to_date('2026-07-23'),
        })

        self.assertIn('2027-01', wizard.detected_registers_preview)
        self.assertNotIn('(Se creará un nuevo registro)', wizard.detected_registers_preview)
