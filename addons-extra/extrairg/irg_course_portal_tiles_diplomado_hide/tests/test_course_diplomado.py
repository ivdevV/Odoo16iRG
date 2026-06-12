# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCourseDiplomado(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCourseDiplomado, cls).setUpClass()
        # Create categories
        cls.categ_diplomado_name = cls.env['product.category'].create({
            'name': 'Diplomado Superior',
        })
        cls.categ_diplomado_code = cls.env['product.category'].create({
            'name': 'Other Categ',
            'code': 'DI-100',
        })
        cls.categ_diplomado_code_d = cls.env['product.category'].create({
            'name': 'Another Categ',
            'code': 'D-200',
        })
        cls.categ_normal = cls.env['product.category'].create({
            'name': 'Normal Category',
            'code': 'NOR',
        })

        # Create products
        cls.product_diplomado_name = cls.env['product.template'].create({
            'name': 'Curso de Diplomado en Psicologia',
            'categ_id': cls.categ_normal.id,
        })
        cls.product_diplomado_categ_name = cls.env['product.template'].create({
            'name': 'Normal Course Product 1',
            'categ_id': cls.categ_diplomado_name.id,
        })
        cls.product_diplomado_categ_code = cls.env['product.template'].create({
            'name': 'Normal Course Product 2',
            'categ_id': cls.categ_diplomado_code.id,
        })
        cls.product_diplomado_categ_code_d = cls.env['product.template'].create({
            'name': 'Normal Course Product 3',
            'categ_id': cls.categ_diplomado_code_d.id,
        })
        cls.product_normal = cls.env['product.template'].create({
            'name': 'Master en Psicologia',
            'categ_id': cls.categ_normal.id,
        })

        # Create course types
        cls.type_di = cls.env['op.course.type'].create({
            'name': 'Some Type',
            'code': 'DI-TYPE',
        })
        cls.type_d = cls.env['op.course.type'].create({
            'name': 'Another Type',
            'code': 'D-TYPE',
        })
        cls.type_diplomado_name = cls.env['op.course.type'].create({
            'name': 'DIPLOMADO DE ESPAÑA',
            'code': 'XYZ',
        })
        cls.type_normal = cls.env['op.course.type'].create({
            'name': 'Master Type',
            'code': 'M-TYPE',
        })

    def test_01_course_code_starts_with_di(self):
        # Course with code starting with 'DI'
        course = self.env['op.course'].create({
            'name': 'Test Course DI Code',
            'code': 'DI-01',
        })
        self.assertTrue(course.is_diplomado(), "Course with code starting with 'DI' should be a diplomado.")

        # Case insensitive check
        course_lower = self.env['op.course'].create({
            'name': 'Test Course di Code',
            'code': 'di-02',
        })
        self.assertTrue(course_lower.is_diplomado(), "Course with code starting with 'di' should be a diplomado.")

    def test_02_course_type_conditions(self):
        # Code starts with 'DI'
        course_type_di = self.env['op.course'].create({
            'name': 'Test Course Type DI',
            'code': 'C-01',
            'course_type_id': self.type_di.id,
        })
        self.assertTrue(course_type_di.is_diplomado())

        # Code starts with 'D'
        course_type_d = self.env['op.course'].create({
            'name': 'Test Course Type D',
            'code': 'C-02',
            'course_type_id': self.type_d.id,
        })
        self.assertTrue(course_type_d.is_diplomado())

        # Name contains 'DIPLOMADO' case insensitive
        course_type_name = self.env['op.course'].create({
            'name': 'Test Course Type Name',
            'code': 'C-03',
            'course_type_id': self.type_diplomado_name.id,
        })
        self.assertTrue(course_type_name.is_diplomado())

    def test_03_product_template_name_contains_diplomado(self):
        # Via product_template_id
        course_product_m2o = self.env['op.course'].create({
            'name': 'Test Course Product M2O',
            'code': 'C-04',
            'product_template_id': self.product_diplomado_name.id,
        })
        self.assertTrue(course_product_m2o.is_diplomado())

        # Via product_template_ids
        course_product_m2m = self.env['op.course'].create({
            'name': 'Test Course Product M2M',
            'code': 'C-05',
            'product_template_ids': [(6, 0, [self.product_diplomado_name.id])],
        })
        self.assertTrue(course_product_m2m.is_diplomado())

    def test_04_product_template_category_conditions(self):
        # Category name contains 'DIPLOMADO'
        course_cat_name = self.env['op.course'].create({
            'name': 'Test Course Categ Name',
            'code': 'C-06',
            'product_template_id': self.product_diplomado_categ_name.id,
        })
        self.assertTrue(course_cat_name.is_diplomado())

        # Category code starts with 'DI'
        course_cat_code_di = self.env['op.course'].create({
            'name': 'Test Course Categ Code DI',
            'code': 'C-07',
            'product_template_id': self.product_diplomado_categ_code.id,
        })
        self.assertTrue(course_cat_code_di.is_diplomado())

        # Category code starts with 'D'
        course_cat_code_d = self.env['op.course'].create({
            'name': 'Test Course Categ Code D',
            'code': 'C-08',
            'product_template_id': self.product_diplomado_categ_code_d.id,
        })
        self.assertTrue(course_cat_code_d.is_diplomado())

    def test_05_normal_course(self):
        # Normal course that should not be detected as diplomado
        course_normal = self.env['op.course'].create({
            'name': 'Test Normal Course',
            'code': 'M-100',
            'course_type_id': self.type_normal.id,
            'product_template_id': self.product_normal.id,
        })
        self.assertFalse(course_normal.is_diplomado(), "A normal course should not be classified as diplomado.")
