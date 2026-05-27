# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
import logging

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestFinancingBackend(TransactionCase):

    def setUp(self):
        super(TestFinancingBackend, self).setUp()
        
        # 1. Partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Checkout Partner',
            'email': 'checkout@example.com',
        })
        
        # 2. Product Attributes setup for 'Planes'
        self.attribute_planes = self.env['product.attribute'].create({
            'name': 'Planes',
            'create_variant': 'always',
        })
        
        self.value_contado = self.env['product.attribute.value'].create({
            'name': 'Contado',
            'attribute_id': self.attribute_planes.id,
        })
        self.value_financed = self.env['product.attribute.value'].create({
            'name': '12 Meses (Financiado)',
            'attribute_id': self.attribute_planes.id,
        })
        
        # 3. Product Template
        self.template = self.env['product.template'].create({
            'name': 'Curso de Prueba Financiación',
            'list_price': 1000.0,
            'sale_ok': True,
            'recurring_invoice': True,
        })
        
        # 4. Attribute Line for Planes
        self.attr_line = self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.template.id,
            'attribute_id': self.attribute_planes.id,
            'value_ids': [(6, 0, [self.value_contado.id, self.value_financed.id])],
        })
        
        # Write extra prices and plazos
        self.ptav_contado = self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', self.template.id),
            ('product_attribute_value_id', '=', self.value_contado.id)
        ])
        self.ptav_financed = self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', self.template.id),
            ('product_attribute_value_id', '=', self.value_financed.id)
        ])
        
        self.ptav_contado.write({
            'plazo': 1,
            'price_extra': 0.0,
        })
        self.ptav_financed.write({
            'plazo': 12,
            'price_extra': 200.0,
        })
        
        # Get variant IDs
        self.product_contado = self.template.product_variant_ids.filtered(
            lambda p: p.product_template_attribute_value_ids.filtered(lambda val: 'contado' in val.name.lower())
        )
        self.product_financed = self.template.product_variant_ids.filtered(
            lambda p: p.product_template_attribute_value_ids.filtered(lambda val: 'contado' not in val.name.lower())
        )
        
        # 5. Financing Product (ensure it exists)
        self.financing_product = self.env.ref('irg_sale_subscription_esp.product_financing_fees', raise_if_not_found=False)
        if not self.financing_product:
            self.financing_product = self.env['product.product'].search([('default_code', '=', 'GASTOS_FIN')], limit=1)
        if not self.financing_product:
            self.financing_product = self.env['product.product'].create({
                'name': 'Gastos de Financiación',
                'default_code': 'GASTOS_FIN',
                'type': 'service',
                'sale_ok': True,
            })
            
        # 6. Matricula Product (ensure it exists)
        self.matricula_product = self.env['product.product'].search([('default_code', '=', 'MATRICULA')], limit=1)
        if not self.matricula_product:
            self.matricula_product = self.env['product.product'].create({
                'name': 'Matrícula',
                'default_code': 'MATRICULA',
                'type': 'service',
                'sale_ok': True,
            })

        # 7. Ensure Recurrence Record exists
        self.recurrence_id = self.env['sale.temporal.recurrence'].search([('duration', '=', 1), ('unit', '=', 'month')], limit=1)
        if not self.recurrence_id:
            self.recurrence_id = self.env['sale.temporal.recurrence'].create({
                'name': 'Mensual',
                'duration': 1,
                'unit': 'month',
            })

        # 8. Ensure Term Schedule & Payment Term exist for 12 Meses
        self.term_schedule_12 = self.env['product.term.schedule'].search([('term_number', '=', 12)], limit=1)
        if not self.term_schedule_12:
            self.term_schedule_12 = self.env['product.term.schedule'].create({
                'name': '12 Meses',
                'term_number': 12,
            })
        self.payment_term_12 = self.env['account.payment.term'].search([('name', '=', '12 Meses')], limit=1)
        if not self.payment_term_12:
            self.payment_term_12 = self.env['account.payment.term'].create({
                'name': '12 Meses',
            })

        # 9. Ensure Term Schedule & Payment Term exist for 1 Mes
        self.term_schedule_1 = self.env['product.term.schedule'].search([('term_number', '=', 1)], limit=1)
        if not self.term_schedule_1:
            self.term_schedule_1 = self.env['product.term.schedule'].create({
                'name': '1 Mes',
                'term_number': 1,
            })
        self.payment_term_1 = self.env['account.payment.term'].search([('name', '=', '1 Mes')], limit=1)
        if not self.payment_term_1:
            self.payment_term_1 = self.env['account.payment.term'].create({
                'name': '1 Mes',
            })

    def test_financing_checkout_flow(self):
        # 1. Create a sale.order manually in draft state
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
        })
        
        # 2. Add an order line with a product that has a financed plan
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_financed.id,
            'product_uom_qty': 1,
            'price_unit': 1200.0,
        })
        
        # 3. Simulate the checkout flow (save/compute)
        order._auto_scheduled_order()
        
        # Refresh cache
        order.invalidate_recordset()
        line.invalidate_recordset()
        
        # 4. Verify that:
        # - The master line unit price is adjusted to cash price (1000.0)
        self.assertEqual(line.price_unit, 1000.0, "The master line unit price was not adjusted to cash price.")
        self.assertEqual(line.irg_line_type, 'master', "The master line type was not marked as master.")
        self.assertTrue(line.irg_force_price_unit_set, "Price unit forcing is not active.")
        self.assertEqual(line.irg_force_price_unit, 1000.0, "Forced price unit is incorrect.")
        
        # - The Gastos de Financiación line was added automatically
        financing_lines = order.order_line.filtered(lambda l: l.irg_line_type == 'financing')
        self.assertEqual(len(financing_lines), 1, "There should be exactly one financing line.")
        self.assertEqual(financing_lines.product_id, self.financing_product, "Incorrect product for financing line.")
        self.assertEqual(financing_lines.price_unit, 200.0, "The financing fee is incorrect.")
        self.assertEqual(financing_lines.irg_parent_line_id, line, "Financing line is not correctly linked to the master line.")
        
        # - The Matrícula (BONIFICADA 100%) line was added automatically
        matricula_lines = order.order_line.filtered(lambda l: l.irg_line_type == 'matricula')
        self.assertEqual(len(matricula_lines), 1, "There should be exactly one matrícula line.")
        self.assertEqual(matricula_lines.product_id, self.matricula_product, "Incorrect product for matrícula line.")
        self.assertEqual(matricula_lines.price_unit, 0.0, "The matrícula price unit should be 0.0.")
        self.assertEqual(matricula_lines.irg_parent_line_id, line, "Matrícula line is not correctly linked to the master line.")
        
        # Verify order term number is 12
        self.assertEqual(order.term_number, 12, "The term number was not updated to 12.")

        # 5. Modify the line to use the cash plan
        line.write({
            'product_id': self.product_contado.id,
        })
        
        # Save/recompute the flow
        order._auto_scheduled_order()
        
        # Refresh cache
        order.invalidate_recordset()
        line.invalidate_recordset()
        
        # 6. Verify that:
        # - The financing line and matrícula line are deleted
        financing_lines_after = order.order_line.filtered(lambda l: l.irg_line_type == 'financing')
        self.assertEqual(len(financing_lines_after), 0, "Financing lines should be deleted.")
        
        matricula_lines_after = order.order_line.filtered(lambda l: l.irg_line_type == 'matricula')
        self.assertEqual(len(matricula_lines_after), 0, "Matrícula lines should be deleted.")
        
        # - The price forcing in the master line is cleared
        self.assertFalse(line.irg_line_type, "Master line type should be cleared (False).")
        self.assertFalse(line.irg_force_price_unit_set, "Price forcing flag should be False.")
        self.assertEqual(line.irg_force_price_unit, 0.0, "Forced price unit should be 0.0.")
        
        # Verify order term number is 1
        self.assertEqual(order.term_number, 1, "The term number was not updated to 1.")
