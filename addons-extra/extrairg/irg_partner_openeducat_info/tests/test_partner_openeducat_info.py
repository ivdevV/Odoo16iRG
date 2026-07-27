# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestPartnerOpenEduCatInfo(TransactionCase):

    def setUp(self):
        super(TestPartnerOpenEduCatInfo, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Student Partner',
            'email': 'teststudent@example.com',
        })
        self.student = self.env['op.student'].create({
            'first_name': 'Test',
            'last_name': 'Student',
            'partner_id': self.partner.id,
            'gr_no': 'TEST-GR-001',
            'sepyc_program': True,
        })

    def test_student_id_computation_and_related_fields(self):
        """Verifica que el partner reconoce el registro op.student y sus campos educativos/accesos."""
        self.assertEqual(self.partner.student_id, self.student, "El partner debe estar enlazado a su op.student")
        self.assertEqual(self.partner.student_gr_no, 'TEST-GR-001', "El campo student_gr_no del partner debe coincidir")
        self.assertTrue(self.partner.student_sepyc_program, "El campo student_sepyc_program debe ser True")

    def test_non_student_partner(self):
        """Verifica que un partner no estudiante tiene student_id igual a False."""
        other_partner = self.env['res.partner'].create({
            'name': 'Regular Contact',
        })
        self.assertFalse(other_partner.student_id, "Un contacto normal no debe tener student_id")
