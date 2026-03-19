from odoo.tests.common import TransactionCase


class TestIrgDiscountException(TransactionCase):
    def test_exception_overrides_product_amount(self):
        ProductTemplate = self.env['product.template']
        Product = self.env['product.product']
        Order = self.env['sale.order']
        OrderLine = self.env['sale.order.line']
        Exception = self.env['irg.discount.exception']
        Program = self.env['irg.discount.program']

        partner = self.env['res.partner'].create({'name': 'Test Partner'})

        tmpl = ProductTemplate.create({'name': 'TP Test Product'})
        prod = Product.create({
            'name': 'TP Test Product',
            'product_tmpl_id': tmpl.id,
            'list_price': 100.0,
            'type': 'product',
            'sale_ok': True,
        })

        order = Order.create({'partner_id': partner.id})
        line = OrderLine.create({
            'order_id': order.id,
            'product_id': prod.id,
            'name': prod.name,
            'product_uom_qty': 2,
            'price_unit': prod.list_price,
        })

        # Create an exception that sets convenio price to 150 for this product
        exc = Exception.create({
            'name': 'Exc Test',
            'product_id': prod.id,
            'price_exception': 150.0,
            'active': True,
        })

        # Create a discount program that uses product_amount
        program = Program.create({
            'name': 'P Test',
            'code': 'PTEST',
            'formula': 'product_amount * 0.1',
            'target_product_ids': [(6, 0, [prod.id])],
        })

        # Re-read order to ensure computed fields are available
        order.invalidate_cache()
        order = Order.browse(order.id)

        discount = program._compute_discount(order)
        expected = round(150.0 * 2 * 0.1, 2)
        self.assertAlmostEqual(discount, expected)
