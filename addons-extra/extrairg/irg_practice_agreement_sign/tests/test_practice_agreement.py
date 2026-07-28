# -*- coding: utf-8 -*-
import base64
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestPracticeAgreement(TransactionCase):

    def setUp(self):
        super(TestPracticeAgreement, self).setUp()
        self.Partner = self.env['res.partner']
        self.PracticeCenter = self.env['practice.center']
        self.Agreement = self.env['practice.agreement']

        # Crear partner y centro de prácticas de prueba
        self.partner = self.Partner.create({
            'name': 'Centro Hospitalario de Prueba S.L.',
            'vat': 'B12345678',
            'email': 'contacto@hospitalprueba.com',
            'phone': '930001122',
        })

        self.center = self.PracticeCenter.create({
            'name': 'Centro Hospitalario de Prueba',
            'official_name': 'Centro Hospitalario de Prueba S.L.',
            'signatory_name': 'Dr. Juan Pérez',
            'partner_id': self.partner.id,
            'street': 'Carrer Major 10',
            'city': 'Barcelona',
            'postal_code': '08001',
            'email': 'contacto@hospitalprueba.com',
            'phone': '930001122',
        })

    def test_01_create_agreement_defaults(self):
        """Verifica la creación del convenio y el arrastre de campos del centro."""
        agreement = self.center.action_create_agreement()
        agreement_rec = self.Agreement.browse(agreement['res_id'])

        self.assertTrue(agreement_rec.name)
        self.assertEqual(agreement_rec.state, 'draft')
        self.assertEqual(agreement_rec.center_official_name, 'Centro Hospitalario de Prueba S.L.')
        self.assertEqual(agreement_rec.signatory_name, 'Dr. Juan Pérez')
        self.assertTrue(agreement_rec.access_token)
        self.assertTrue(agreement_rec.signature_irg, "La firma oficial por defecto de Raimon Gaja debe estar cargada.")

    def test_02_portal_url_and_token(self):
        """Verifica la generación del token seguro y URL del portal."""
        agreement = self.Agreement.create({
            'practice_center_id': self.center.id,
            'center_official_name': self.center.name,
        })
        url = agreement.get_portal_url()
        self.assertIn('/convenio/firma/', url)
        self.assertIn(agreement.access_token, url)

    def test_03_action_complete_signature(self):
        """Prueba la acción de firma digital, cambio de estado y adjuntado del PDF."""
        agreement = self.Agreement.create({
            'practice_center_id': self.center.id,
            'center_official_name': self.center.name,
            'signatory_name': 'Dr. Juan Pérez',
            'email': 'contacto@hospitalprueba.com',
        })

        # Base64 ficticio de firma PNG de 1px
        dummy_signature = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        agreement.action_complete_signature(
            signature_base64=dummy_signature,
            signer_name='Dr. Juan Pérez',
            ip_address='192.168.1.50'
        )

        self.assertEqual(agreement.state, 'completed')
        self.assertEqual(agreement.signed_by, 'Dr. Juan Pérez')
        self.assertEqual(agreement.signed_ip, '192.168.1.50')
        self.assertTrue(agreement.signed_on)
        self.assertTrue(agreement.signature_center)
        self.assertTrue(agreement.pdf_attachment_id, "Se debe generar el adjunto PDF del convenio.")
