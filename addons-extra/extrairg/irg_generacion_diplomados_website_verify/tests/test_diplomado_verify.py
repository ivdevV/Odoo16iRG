# -*- coding: utf-8 -*-
import json

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install', 'irg_generacion_diplomados_website_verify')
class TestDiplomadoWebsiteVerify(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['irg.diplomado.registry'].sudo().search([('name', '=', 'DIP-VERIFY-TEST')]).unlink()
        cls.env['op.student'].sudo().search([('first_name', '=', 'VerifyDiplomado')]).unlink()
        cls.env['op.course'].sudo().search([('name', '=', 'Diplomado Verify Test')]).unlink()
        cls.env['res.partner'].sudo().search([('email', '=', 'verify.diplomado@example.test')]).unlink()

        cls.env['ir.config_parameter'].sudo().set_param('web.base.url', 'https://odoo.example.test')
        cls.partner = cls.env['res.partner'].sudo().create({
            'name': 'VerifyDiplomado Student',
            'email': 'verify.diplomado@example.test',
        })
        cls.student = cls.env['op.student'].sudo().create({
            'partner_id': cls.partner.id,
            'first_name': 'VerifyDiplomado',
            'last_name': 'Student',
        })
        cls.course = cls.env['op.course'].sudo().create({
            'name': 'Diplomado Verify Test',
            'code': 'DIPVERIFY',
        })
        cls.diplomado_registry = cls.env['irg.diplomado.registry'].sudo().create({
            'name': 'DIP-VERIFY-TEST',
            'student_id': cls.student.id,
            'student_name': cls.student.name,
            'course_id': cls.course.id,
            'diplomado_name': cls.course.name,
            'issue_date': '2026-06-16',
            'diploma_type': 'digital',
        })
        cls.env.cr.commit()

    def test_qr_url_uses_odoo_website_verification_route(self):
        qr_url = self.diplomado_registry._build_diplomado_verification_qr_url()
        self.assertIn('https://odoo.example.test/verificar/?', qr_url)
        self.assertIn('id=DIP-VERIFY-TEST', qr_url)

    def test_public_verify_page_finds_diplomado_registry(self):
        self.authenticate('admin', 'admin')
        response = self.url_open('/verificar/?id=DIP-VERIFY-TEST')
        self.assertEqual(response.status_code, 200)
        self.assertIn('ENCONTRADO', response.text)
        self.assertIn('Diplomado Verify Test', response.text)

    def test_public_verify_api_finds_diplomado_registry(self):
        self.authenticate('admin', 'admin')
        response = self.url_open('/verificar_api/?id=DIP-VERIFY-TEST')
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.text)
        self.assertTrue(payload['found'])
        self.assertEqual(payload['source'], 'odoo_diplomado_registry')
        self.assertEqual(payload['document_type'], 'diplomado')
