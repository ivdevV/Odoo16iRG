# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields


class TestIntensivoModality(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Partner = self.env['res.partner']
        self.ProductTemplate = self.env['product.template']
        self.ProductProduct = self.env['product.product']
        self.ProductAttribute = self.env['product.attribute']
        self.ProductAttributeValue = self.env['product.attribute.value']
        self.ProductTemplateAttributeLine = self.env['product.template.attribute.line']
        self.OpCourse = self.env['op.course']
        self.OpBatch = self.env['op.batch']
        self.OpModality = self.env['op.modality']
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']

        # Category for master oficial
        self.master_category = self.env['product.category'].create({
            'name': 'Master Oficial Category',
            'code': 'MO',
        })

        # Course PC
        self.course_pc = self.OpCourse.create({
            'name': 'Máster Oficial PC',
            'code': 'PC',
            'lang': 'en_US',
        })

        # Modality attribute
        self.attr_modalidad = self.ProductAttribute.create({
            'name': 'Modalidad',
        })
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

        # Product template with variant
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

        # Retrieve product variant with Intensivo
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

        self.customer = self.Partner.create({'name': 'Test Student Intensivo'})

    def test_get_lot_id_mopcin2701(self):
        """Test get_lot_id for course PC with Intensivo (IN) modality and date 2027-01-01 generates MOPCIN2701."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'admission_date': fields.Date.to_date('2027-01-01'),
        })
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product_variant.id,
            'product_uom_qty': 1,
            'price_unit': 1000.0,
            'start_date_enroller': fields.Date.to_date('2027-01-01'),
        })

        batch = order.with_context(irg_get_lot_line_id=line.id).get_lot_id(self.course_pc)
        self.assertTrue(batch, "Batch should be created or found")
        self.assertEqual(batch.code, 'MOPCIN2701', f"Expected batch code MOPCIN2701, got {batch.code}")
        self.assertEqual(batch.start_date, fields.Date.to_date('2027-01-01'))
        self.assertEqual(batch.date_start_class, fields.Date.to_date('2027-01-01'))
        self.assertTrue(getattr(batch, 'irg_is_intensive', False), "Batch should be flagged as intensive")

    def test_get_lot_id_with_sale_order_tick_is_intensive(self):
        """Test get_lot_id when irg_is_intensive is checked directly on sale.order."""
        product_generic = self.ProductProduct.create({
            'name': 'Programa Máster Oficial Genérico',
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
            'price_unit': 1000.0,
            'start_date_enroller': fields.Date.to_date('2027-01-01'),
        })

        batch = order.with_context(irg_get_lot_line_id=line.id).get_lot_id(self.course_pc)
        self.assertTrue(batch, "Batch should be created or found")
        self.assertEqual(batch.code, 'MOPCIN2701', f"Expected batch code MOPCIN2701 from tick, got {batch.code}")
        self.assertTrue(getattr(batch, 'irg_is_intensive', False), "Batch should be flagged as intensive")
