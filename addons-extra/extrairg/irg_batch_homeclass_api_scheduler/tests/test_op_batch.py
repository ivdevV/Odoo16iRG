# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestOpBatchHomeClass(TransactionCase):

    def setUp(self):
        super(TestOpBatchHomeClass, self).setUp()
        
        # Crear un curso para asociarlo a los lotes
        self.course = self.env['op.course'].create({
            'name': 'Curso de Test',
            'code': 'TEST-CURSE',
        })
        
        # Buscar o crear modalidad HomeClass
        self.modality_hc = self.env['op.modality'].search([('code', '=', 'HC')], limit=1)
        if not self.modality_hc:
            self.modality_hc = self.env['op.modality'].create({
                'name': 'HomeClass',
                'code': 'HC',
                'new_code': 'HC',
                'analytic_code': 'HC',
            })

    def test_01_homeclass_batch_positive(self):
        """Un lote con modalidad HC y código estándar debe ser HomeClass"""
        batch = self.env['op.batch'].create({
            'name': 'Lote HC Test',
            'code': 'HC-TEST-01',
            'modality_id': self.modality_hc.id,
            'course_id': self.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        self.assertTrue(batch.is_homeclass_batch, "El lote con código HC-TEST-01 y modalidad HC debe ser HomeClass")

    def test_02_homeclass_batch_excluded_by_di_code(self):
        """Un lote cuyo código empieza por DI no debe ser HomeClass, aunque tenga modalidad HC"""
        batch = self.env['op.batch'].create({
            'name': 'Lote DI Test',
            'code': 'DI-TEST-01',
            'modality_id': self.modality_hc.id,
            'course_id': self.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        self.assertFalse(batch.is_homeclass_batch, "El lote con código DI-TEST-01 no debe ser HomeClass aunque tenga modalidad HC")

    def test_03_homeclass_batch_excluded_by_di_code_case_insensitive(self):
        """Un lote cuyo código empieza por di/Di/dI no debe ser HomeClass"""
        batch = self.env['op.batch'].create({
            'name': 'Lote di Test',
            'code': 'di-TEST-02',
            'modality_id': self.modality_hc.id,
            'course_id': self.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        self.assertFalse(batch.is_homeclass_batch, "El lote con código di-TEST-02 no debe ser HomeClass")

    def test_04_homeclass_batch_write_di_excludes(self):
        """Si se modifica el código de un lote a uno que empiece por DI, se debe actualizar is_homeclass_batch a False"""
        batch = self.env['op.batch'].create({
            'name': 'Lote Modificación Test',
            'code': 'HC-TEST-03',
            'modality_id': self.modality_hc.id,
            'course_id': self.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        self.assertTrue(batch.is_homeclass_batch)
        
        batch.write({'code': 'DI-TEST-03'})
        self.assertFalse(batch.is_homeclass_batch, "Al cambiar el código a DI-TEST-03, el lote debe dejar de ser HomeClass")
