# -*- coding: utf-8 -*-

import json
from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestOficialidadWebhook(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = cls.env['op.course'].create({
            'name': 'Curso Oficialidad',
            'code': 'OFI-01',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Producto Oficialidad',
            'type': 'service',
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'Registro Oficialidad',
            'course_id': cls.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Alumna Vinculada',
            'email': 'alumna@example.com',
        })
        cls.student = cls.env['op.student'].create({
            'partner_id': cls.partner.id,
            'first_name': 'Alumna',
            'last_name': 'Vinculada',
            'birth_date': '2000-01-01',
            'gender': 'f',
        })
        common_values = {
            'birth_date': '2000-01-01',
            'gender': 'o',
            'register_id': cls.register.id,
            'course_id': cls.course.id,
            'application_date': '2026-07-01 10:00:00',
        }
        cls.admission_linked = cls.env['op.admission'].create({
            **common_values,
            'name': 'Alumna Vinculada',
            'first_name': 'Alumna',
            'last_name': 'Vinculada',
            'email': 'alumna@example.com',
            'student_id': cls.student.id,
            'partner_id': cls.partner.id,
        })
        cls.admission_unlinked = cls.env['op.admission'].create({
            **common_values,
            'name': 'Alumno Sin Vínculos',
            'first_name': 'Alumno',
            'last_name': 'Sin Vínculos',
            'email': 'sin-vinculos@example.com',
        })
        cls.params = cls.env['ir.config_parameter'].sudo()
        cls.params.set_param(
            'irg_oficialidad_webhook.webhook_url',
            'https://n8n.example.test/oficialidad',
        )
        cls.params.set_param('irg_oficialidad_webhook.auth_token', 'test-token')
        cls.params.set_param('irg_oficialidad_webhook.timeout', '15')

    def _new_wizard(self, admissions=None):
        values = {}
        if admissions is not None:
            values['admission_ids'] = [(6, 0, admissions.ids)]
        return self.env['oficialidad.send.wizard'].with_context(
            active_model='op.admission.register',
            active_id=self.register.id,
        ).create(values)

    def test_wizard_precarga(self):
        wizard = self._new_wizard()

        self.assertEqual(wizard.register_id, self.register)
        self.assertEqual(wizard.admission_ids, self.register.admission_ids)

    def test_payload_serializacion_completa(self):
        captured = {}

        def capture_post(webhook_url, payload_json, auth_token, timeout):
            captured['webhook_url'] = webhook_url
            captured['payload_json'] = payload_json
            captured['auth_token'] = auth_token
            captured['timeout'] = timeout
            return 200, '{"ok": true}'

        service = self.env['irg.oficialidad.webhook.service']
        with patch.object(type(service), '_post_json', side_effect=capture_post):
            service.send_oficialidad(self.register, self.register.admission_ids)

        payload = json.loads(captured['payload_json'])
        self.assertEqual(
            set(payload), {'odoo', 'register', 'students', 'sent_at', 'sent_by'}
        )
        self.assertEqual(payload['register']['id'], self.register.id)
        self.assertEqual(len(payload['students']), 2)
        by_admission_id = {
            row['admission']['id']: row for row in payload['students']
        }
        linked = by_admission_id[self.admission_linked.id]
        unlinked = by_admission_id[self.admission_unlinked.id]
        for row in payload['students']:
            self.assertEqual(set(row), {'admission', 'student', 'partner'})
            self.assertTrue(row['admission'])
            self.assertIn('application_number', row['admission'])
            self.assertIn('name', row['admission'])
            self.assertIn('state', row['admission'])
            for record_payload in row.values():
                self.assertNotIn('image', record_payload)
                self.assertNotIn('image_1920', record_payload)
                self.assertNotIn('message_ids', record_payload)
                self.assertNotIn('activity_ids', record_payload)
                self.assertNotIn('website_message_ids', record_payload)
        self.assertTrue(linked['student'])
        self.assertTrue(linked['partner'])
        self.assertEqual(linked['partner']['name'], self.partner.name)
        self.assertEqual(linked['partner']['email'], self.partner.email)
        self.assertEqual(unlinked['student'], {})
        self.assertEqual(unlinked['partner'], {})
        json.dumps(payload)

    def test_serializacion_omite_campo_que_falla(self):
        class ProblematicRecord:
            _fields = {'broken_compute': SimpleNamespace(type='char')}

            def __bool__(self):
                return True

            def ensure_one(self):
                return self

            def __getitem__(self, field_name):
                raise RuntimeError('compute roto')

        service = self.env['irg.oficialidad.webhook.service']

        self.assertEqual(service._serialize_record(ProblematicRecord()), {})

    def test_envio_2xx_marca_solo_seleccionadas(self):
        wizard = self._new_wizard(self.admission_linked)
        service = self.env['irg.oficialidad.webhook.service']

        with patch.object(type(service), '_post_json', return_value=(204, '')):
            action = wizard.action_send()

        self.assertTrue(self.admission_linked.oficialidad_sent_date)
        self.assertFalse(self.admission_unlinked.oficialidad_sent_date)
        self.assertEqual(action['tag'], 'display_notification')

    def test_respuesta_no_2xx_no_marca_admisiones(self):
        wizard = self._new_wizard(self.register.admission_ids)
        service = self.env['irg.oficialidad.webhook.service']

        with patch.object(type(service), '_post_json', return_value=(500, 'error')):
            with self.assertRaises(UserError):
                wizard.action_send()

        self.assertFalse(self.admission_linked.oficialidad_sent_date)
        self.assertFalse(self.admission_unlinked.oficialidad_sent_date)

    def test_sin_config_no_marca_admisiones(self):
        self.params.set_param('irg_oficialidad_webhook.webhook_url', '')
        self.params.set_param('irg_oficialidad_webhook.auth_token', '')
        wizard = self._new_wizard(self.register.admission_ids)

        with self.assertRaises(UserError):
            wizard.action_send()

        self.assertFalse(self.admission_linked.oficialidad_sent_date)
        self.assertFalse(self.admission_unlinked.oficialidad_sent_date)

    def test_seleccion_vacia(self):
        wizard = self._new_wizard(self.env['op.admission'])

        with self.assertRaises(UserError):
            wizard.action_send()
