# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo import fields

_logger = logging.getLogger(__name__)

# Tag propio para poder ejecutar esta clase de forma aislada:
# --test-tags irg_gender
@tagged('irg_gender', 'post_install', '-at_install')
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

        # Rango relativo a "hoy" (en vez de fechas fijas) para que
        # application_date (default=Datetime.now()) siempre caiga dentro del
        # registro, sin importar cuándo se ejecute la suite.
        today = fields.Date.today()
        self.register = self.env['op.admission.register'].create({
            'name': 'Test Register G',
            'course_id': self.course.id,
            'period': '2026-06',
            'start_date': today - timedelta(days=30),
            'end_date': today + timedelta(days=30),
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })

        self.batch = self.env['op.batch'].create({
            'name': 'Test Batch G',
            'code': 'TST-BG-01',
            'course_id': self.course.id,
            'start_date': today - timedelta(days=30),
            'end_date': today + timedelta(days=180),
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

    def test_06_student_gender_over_order(self):
        """A2: el género del estudiante (partner de la admisión) gana sobre el
        género del pedido (self.gender), vía el helper
        _irg_resolve_admission_gender de isep_openeducat_sale.

        Se ejercita el helper directamente sobre un sale.order (en vez de
        montar todo el flujo de confirmación/admisión de una venta, más
        frágil de fixturar en este entorno), porque el helper es el único
        punto donde se decide la prioridad estudiante > pedido (R1).
        """
        partner_payer = self.env['res.partner'].create({
            'name': 'Payer Male',
            'gender': 'm',
        })
        partner_student = self.env['res.partner'].create({
            'name': 'Student Female',
            'gender': 'f',
        })

        order = self.env['sale.order'].create({
            'partner_id': partner_payer.id,
            'gender': 'm',
        })

        # Pedido dice 'm' (pagador), pero el estudiante real es 'f': debe ganar 'f'.
        resolved = order._irg_resolve_admission_gender(partner_student)
        self.assertEqual(resolved, 'f')

        # Sin partner explícito, cae al partner_id del pedido (pagador == 'm').
        resolved_default = order._irg_resolve_admission_gender()
        self.assertEqual(resolved_default, 'm')

    def test_07_explicit_other_not_overwritten(self):
        """A3: 'o' explícito en create/write de op.admission no se sobreescribe
        por la adivinación de nombre/título, aunque el nombre sugiera 'f'/'m'."""
        # "Laura Gomez" adivinaría 'f' (ver test_05), pero el 'o' explícito debe prevalecer.
        partner = self.env['res.partner'].create({
            'name': 'Laura Gomez',
        })

        admission = self.env['op.admission'].create({
            'name': 'Laura Gomez',
            'first_name': 'Laura',
            'last_name': 'Gomez',
            'partner_id': partner.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
            'gender': 'o',
        })
        self.assertEqual(admission.gender, 'o')

        # Repetimos en write: forzar primero a 'm' y luego escribir 'o' explícito.
        admission.write({'gender': 'm'})
        self.assertEqual(admission.gender, 'm')
        admission.write({'gender': 'o'})
        self.assertEqual(admission.gender, 'o')

    def test_08_moodle_value_mapped_by_helper(self):
        """A4: un partner con valor Moodle 'female' se resuelve a 'f' a través
        del helper _irg_resolve_admission_gender (mapeo hecho en el helper, sin
        depender de la intercepción de irg_admission_gender_fix)."""
        partner = self.env['res.partner'].create({
            'name': 'Moodle Female Partner',
            'gender': 'female',
        })

        order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })

        resolved = order._irg_resolve_admission_gender(partner)
        self.assertEqual(resolved, 'f')

        # Complementariamente: la admisión creada con ese valor resuelto por el
        # helper (patrón usado en los módulos de venta: helper(...) or 'o')
        # también queda en 'f'.
        admission = self.env['op.admission'].create({
            'name': partner.name,
            'first_name': 'Moodle',
            'last_name': 'Female',
            'partner_id': partner.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'fees_term_id': self.fees_term.id,
            'gender': order._irg_resolve_admission_gender(partner) or 'o',
        })
        self.assertEqual(admission.gender, 'f')
