# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestGenderMapping(TransactionCase):

    def setUp(self):
        super(TestGenderMapping, self).setUp()

        self.course = self.env['op.course'].create({
            'name': 'Test Course',
            'code': 'T-CR-G',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Course Product G',
            'type': 'service',
        })

        self.register = self.env['op.admission.register'].create({
            'name': 'Test Register G',
            'course_id': self.course.id,
            'period': '2026-06',
            'start_date': '2026-06-01',
            'end_date': '2026-06-30',
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })

        self.batch = self.env['op.batch'].create({
            'name': 'Test Batch G',
            'code': 'TST-BG-01',
            'course_id': self.course.id,
            'start_date': '2026-06-01',
            'end_date': '2026-12-31',
        })

        self.fees_term = self.env['op.fees.terms'].search([], limit=1)
        if not self.fees_term:
            self.fees_term = self.env['op.fees.terms'].create({
                'name': 'Test Fees Term G',
                'fees_terms': 'fixed_days',
            })

    def test_01_create_admission_explicit_gender(self):
        """Test mapping when explicit gender is provided in create."""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner Explicit',
        })
        
        admission_male = self.env['op.admission'].create({
            'name': 'Test Male',
            'first_name': 'Test',
            'last_name': 'Male',
            'partner_id': partner.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
            'gender': 'male',
        })
        self.assertEqual(admission_male.gender, 'm')

        admission_female = self.env['op.admission'].create({
            'name': 'Test Female',
            'first_name': 'Test',
            'last_name': 'Female',
            'partner_id': partner.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
            'gender': 'female',
        })
        self.assertEqual(admission_female.gender, 'f')

    def test_02_create_admission_from_partner_gender(self):
        """Test mapping from partner gender when no explicit gender or default 'o' is provided."""
        partner_male = self.env['res.partner'].create({
            'name': 'Partner Male',
        })
        if hasattr(partner_male, 'gender_type'):
            partner_male.write({'gender_type': 'male'})
        else:
            partner_male.write({'gender': 'm'})

        partner_female = self.env['res.partner'].create({
            'name': 'Partner Female',
        })
        if hasattr(partner_female, 'gender_type'):
            partner_female.write({'gender_type': 'female'})
        else:
            partner_female.write({'gender': 'f'})

        admission_male = self.env['op.admission'].create({
            'name': 'Test Male Partner',
            'first_name': 'Test',
            'last_name': 'MalePartner',
            'partner_id': partner_male.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission_male.gender, 'm')

        admission_female = self.env['op.admission'].create({
            'name': 'Test Female Partner',
            'first_name': 'Test',
            'last_name': 'FemalePartner',
            'partner_id': partner_female.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
            'gender': 'o',
        })
        self.assertEqual(admission_female.gender, 'f')

    def test_03_write_admission_gender(self):
        """Test mapping during write operations on admission."""
        partner_male = self.env['res.partner'].create({
            'name': 'Partner Male W',
        })
        if hasattr(partner_male, 'gender_type'):
            partner_male.write({'gender_type': 'male'})
        else:
            partner_male.write({'gender': 'm'})

        partner_female = self.env['res.partner'].create({
            'name': 'Partner Female W',
        })
        if hasattr(partner_female, 'gender_type'):
            partner_female.write({'gender_type': 'female'})
        else:
            partner_female.write({'gender': 'f'})

        admission = self.env['op.admission'].create({
            'name': 'Test Write',
            'first_name': 'Test',
            'last_name': 'Write',
            'partner_id': partner_male.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission.gender, 'm')

        admission.write({'gender': 'female'})
        self.assertEqual(admission.gender, 'f')

        admission.write({'partner_id': partner_female.id})
        self.assertEqual(admission.gender, 'f')

    def test_04_student_gender_mapping(self):
        """Test mapping on op.student creation and modification."""
        partner_male = self.env['res.partner'].create({
            'name': 'Partner Student Male',
        })
        if hasattr(partner_male, 'gender_type'):
            partner_male.write({'gender_type': 'male'})
        else:
            partner_male.write({'gender': 'm'})

        student = self.env['op.student'].create({
            'name': 'Test Student',
            'first_name': 'Test',
            'last_name': 'Student',
            'partner_id': partner_male.id,
            'birth_date': '2000-01-01',
        })
        self.assertEqual(student.gender, 'm')

        student.write({'gender': 'female'})
        self.assertEqual(student.gender, 'f')

    def test_05_intelligent_gender_guessing(self):
        """Test intelligent gender guessing from partner's name and title."""
        # 1. Test by title
        title_female = self.env['res.partner.title'].create({'name': 'Sra.', 'shortcut': 'Sra.'})
        partner_title_f = self.env['res.partner'].create({
            'name': 'Guadalupe Ortiz',
            'title': title_female.id,
        })
        admission_title_f = self.env['op.admission'].create({
            'name': 'Guadalupe Ortiz',
            'first_name': 'Guadalupe',
            'last_name': 'Ortiz',
            'partner_id': partner_title_f.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission_title_f.gender, 'f')

        # 2. Test by exact dictionary match
        partner_name_f = self.env['res.partner'].create({
            'name': 'Laura Gomez',
        })
        admission_name_f = self.env['op.admission'].create({
            'name': 'Laura Gomez',
            'first_name': 'Laura',
            'last_name': 'Gomez',
            'partner_id': partner_name_f.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission_name_f.gender, 'f')

        partner_name_m = self.env['res.partner'].create({
            'name': 'Juan Pérez',
        })
        admission_name_m = self.env['op.admission'].create({
            'name': 'Juan Pérez',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'partner_id': partner_name_m.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission_name_m.gender, 'm')

        # 3. Test by ending heuristics
        partner_heuristic_f = self.env['res.partner'].create({
            'name': 'Carla Ruiz',
        })
        admission_heuristic_f = self.env['op.admission'].create({
            'name': 'Carla Ruiz',
            'first_name': 'Carla',
            'last_name': 'Ruiz',
            'partner_id': partner_heuristic_f.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission_heuristic_f.gender, 'f')

        partner_heuristic_m = self.env['res.partner'].create({
            'name': 'Roberto Diaz',
        })
        admission_heuristic_m = self.env['op.admission'].create({
            'name': 'Roberto Diaz',
            'first_name': 'Roberto',
            'last_name': 'Diaz',
            'partner_id': partner_heuristic_m.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission_heuristic_m.gender, 'm')

        # 4. Test fallback
        partner_other = self.env['res.partner'].create({
            'name': 'Xyz Unknown',
        })
        admission_other = self.env['op.admission'].create({
            'name': 'Xyz Unknown',
            'first_name': 'Xyz',
            'last_name': 'Unknown',
            'partner_id': partner_other.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
        })
        self.assertEqual(admission_other.gender, 'o')
