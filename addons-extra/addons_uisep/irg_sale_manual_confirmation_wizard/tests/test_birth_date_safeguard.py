# -*- coding: utf-8 -*-
from datetime import date
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestBirthDateSafeguard(TransactionCase):

    def setUp(self):
        super(TestBirthDateSafeguard, self).setUp()

        self.titular_partner = self.env['res.partner'].create({
            'name': 'Titular Comprador',
            'email': 'titular@example.com',
            'birth_date': '1975-01-01',
        })

        self.student_partner = self.env['res.partner'].create({
            'name': 'Alumno Estudiante Real',
            'email': 'alumno_real@example.com',
            'birth_date': '1998-08-15',
        })

        self.course = self.env['op.course'].create({
            'name': 'Curso Test Nacimiento',
            'code': 'CT-NAC',
        })

        self.product = self.env['product.product'].create({
            'name': 'Producto Curso Nacimiento',
            'type': 'service',
        })

        self.register = self.env['op.admission.register'].create({
            'name': 'Registro Test Nacimiento',
            'course_id': self.course.id,
            'period': '2026-05',
            'start_date': '2026-05-01',
            'end_date': '2026-06-30',
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })

        self.batch = self.env['op.batch'].create({
            'name': 'Lote Test Nacimiento',
            'code': 'LT-NAC-01',
            'course_id': self.course.id,
            'start_date': '2026-06-01',
            'end_date': '2026-12-31',
        })

    def test_student_birth_date_preserved_when_student_differs_from_titular(self):
        """Verificar que al tener alumno diferente al titular, NO se sobrescriba la fecha del alumno
        con Date.today() ni con la fecha del titular ni con 2000-01-01.
        """
        # Crear presupuesto donde partner_id es el titular y student_id es el alumno
        order = self.env['sale.order'].create({
            'partner_id': self.titular_partner.id,
            'student_id': self.student_partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

        # Confirmar el pedido utilizando la lógica del wizard manual
        wizard = self.env['irg.manual.confirmation.wizard'].create({
            'order_id': order.id,
            'admission_date': date(2026, 5, 15),
        })
        wizard.action_confirm()

        # Comprobar que la fecha de nacimiento del estudiante no se corrompió a la fecha de hoy
        self.assertEqual(
            str(self.student_partner.birth_date),
            '1998-08-15',
            "La fecha de nacimiento del alumno se corrompió tras la confirmación."
        )

        # Comprobar que la admisión creada tiene la fecha de nacimiento real del alumno
        admission = self.env['op.admission'].search([('order_id', '=', order.id)], limit=1)
        if admission:
            self.assertEqual(
                str(admission.birth_date),
                '1998-08-15',
                "La admisión no recibió la fecha de nacimiento correcta del alumno."
            )

    def test_submit_form_does_not_erase_partner_birth_date_with_false(self):
        """Verificar que si op.admission tiene birth_date False, submit_form() NO borre la fecha
        existente en res.partner a False.
        """
        partner = self.env['res.partner'].create({
            'name': 'Alumno Con Fecha Previa',
            'email': 'alumno_fecha_previa@example.com',
            'birth_date': '1995-12-25',
        })

        admission = self.env['op.admission'].create({
            'name': partner.name,
            'first_name': 'Alumno',
            'last_name': 'Fecha Previa',
            'email': partner.email,
            'partner_id': partner.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'application_date': '2026-05-15',
        })
        # Forzar birth_date de admisión a False para simular admisión sin fecha
        admission.sudo().write({'birth_date': False})

        # Invocamos submit_form()
        admission.submit_form()

        # Comprobar que partner.birth_date sigue conservando 1995-12-25 y NO se borró a False
        self.assertEqual(
            str(partner.birth_date),
            '1995-12-25',
            "submit_form() borró la fecha de nacimiento real del contacto a False."
        )
