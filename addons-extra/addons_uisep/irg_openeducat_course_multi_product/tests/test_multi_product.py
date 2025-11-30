from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestCourseMultiProduct(TransactionCase):

    def setUp(self):
        super(TestCourseMultiProduct, self).setUp()
        self.OpCourse = self.env['op.course']
        self.Product = self.env['product.template']
        self.AdmissionRegister = self.env['op.admission.register']
        self.SaleOrder = self.env['sale.order']
        self.Partner = self.env['res.partner']

        # Create Products
        self.product1 = self.Product.create({'name': 'Course Product 1', 'is_academic_program': True, 'recurring_invoice': True})
        self.product2 = self.Product.create({'name': 'Course Product 2', 'is_academic_program': True, 'recurring_invoice': True})

        # Create Course with multiple products
        self.course = self.OpCourse.create({
            'name': 'Test Multi Product Course',
            'code': 'TMPC',
            'product_template_ids': [(6, 0, [self.product1.id, self.product2.id])]
        })

        # Create Partner
        self.partner = self.Partner.create({'name': 'Test Student'})

    def test_course_products(self):
        """Test that course has multiple products"""
        self.assertIn(self.product1, self.course.product_template_ids)
        self.assertIn(self.product2, self.course.product_template_ids)

    def test_admission_register_creation(self):
        """Test admission register creation and validation"""
        register = self.AdmissionRegister.create({
            'name': 'Test Register',
            'course_id': self.course.id,
            'period': '2025-01',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'min_count': 1,
            'max_count': 10
        })
        # Check if products are synced
        self.assertIn(self.product1, register.product_template_ids)
        self.assertIn(self.product2, register.product_template_ids)

    def test_sale_order_link(self):
        """Test sale order linking to course and register"""
        # Create Register
        register = self.AdmissionRegister.create({
            'name': 'Test Register',
            'course_id': self.course.id,
            'period': '2025-01',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'state': 'confirm'
        })

        # Create Sale Order for Product 1
        so1 = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'admission_date': '2025-01-15',
            'order_line': [(0, 0, {
                'product_id': self.product1.product_variant_id.id,
                'product_template_id': self.product1.id
            })]
        })
        so1._compute_period() # Trigger period computation
        so1.get_academic_product_template_id()
        so1.get_register_id(so1.period, self.product1)

        self.assertEqual(so1.course_id, self.course)
        self.assertEqual(so1.admission_register_id, register)

        # Create Sale Order for Product 2
        so2 = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'admission_date': '2025-01-15',
            'order_line': [(0, 0, {
                'product_id': self.product2.product_variant_id.id,
                'product_template_id': self.product2.id
            })]
        })
        so2._compute_period()
        so2.get_academic_product_template_id()
        so2.get_register_id(so2.period, self.product2)

        self.assertEqual(so2.course_id, self.course)
        self.assertEqual(so2.admission_register_id, register)
