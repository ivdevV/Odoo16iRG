# -*- coding: utf-8 -*-

import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib import error as url_error

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..models import irg_oficialidad_webhook_service as service_module


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
            'https://8.8.8.8/oficialidad',
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

        def capture_post(
            webhook_url,
            payload_json,
            auth_token,
            timeout,
            pinned_ip=None,
            server_hostname=None,
        ):
            captured['webhook_url'] = webhook_url
            captured['payload_json'] = payload_json
            captured['auth_token'] = auth_token
            captured['timeout'] = timeout
            captured['pinned_ip'] = pinned_ip
            captured['server_hostname'] = server_hostname
            return 200, '{"ok": true}'

        service = self.env['irg.oficialidad.webhook.service']
        with patch.object(type(service), '_post_json', side_effect=capture_post):
            service.send_oficialidad(self.register, self.register.admission_ids)

        payload = json.loads(captured['payload_json'])
        self.assertEqual(
            set(payload), {'odoo', 'register', 'students', 'sent_at', 'sent_by'}
        )
        self.assertEqual(payload['register']['id'], self.register.id)
        self.assertEqual(captured['pinned_ip'], '8.8.8.8')
        self.assertEqual(captured['server_hostname'], '8.8.8.8')
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

    def test_serializacion_excluye_credenciales_dinamicas(self):
        values = {
            'signup_token': 'signup-secret',
            'signup_type': 'reset',
            'signup_expiration': 'tomorrow',
            'new_password_user': 'new-secret',
            'password': 'password-secret',
            'SessionToken': 'session-secret',
            'client_secret': 'client-secret',
            'PASSWD_HASH': 'passwd-secret',
            'ApiKey': 'api-secret',
            'privateKeyPem': 'private-key-secret',
            'external_credential': 'credential-secret',
            'business_key': 'ordinary-business-value',
            'key_account': 'ordinary-account-value',
        }

        class DynamicRecord:
            _fields = {
                name: SimpleNamespace(type='char') for name in values
            }

            def __bool__(self):
                return True

            def ensure_one(self):
                return self

            def __getitem__(self, field_name):
                return values[field_name]

        payload = self.env[
            'irg.oficialidad.webhook.service'
        ]._serialize_record(DynamicRecord())

        self.assertEqual(payload, {
            'business_key': 'ordinary-business-value',
            'key_account': 'ordinary-account-value',
        })

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

    def test_usuario_no_administrador_no_puede_usar_wizard(self):
        admission_user_group = self.env.ref(
            'openeducat_admission.group_op_admission_user'
        )
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Usuario admisiones sin privilegios',
            'login': 'oficialidad-no-admin@example.com',
            'groups_id': [(6, 0, [admission_user_group.id])],
        })
        wizard_model = self.env['oficialidad.send.wizard'].with_user(user)
        self.assertFalse(
            wizard_model.check_access_rights('create', raise_exception=False)
        )
        with self.assertRaises(AccessError):
            wizard_model.with_context(
                active_model='op.admission.register',
                active_id=self.register.id,
            ).default_get(['register_id', 'admission_ids'])
        wizard = self._new_wizard(self.admission_linked).with_user(user)
        service = self.env['irg.oficialidad.webhook.service']
        with patch.object(type(service), '_post_json', return_value=(200, '{}')):
            with self.assertRaises(AccessError):
                wizard.action_send()
            with self.assertRaises(AccessError):
                service.with_user(user).send_oficialidad(
                    self.register, self.admission_linked
                )

    def test_seleccion_forjada_de_otro_registro_se_rechaza(self):
        other_register = self.env['op.admission.register'].create({
            'name': 'Otro registro',
            'course_id': self.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })
        other_admission = self.env['op.admission'].create({
            'name': 'Alumno de otro registro',
            'first_name': 'Alumno',
            'last_name': 'Otro Registro',
            'email': 'otro-registro@example.com',
            'birth_date': '2000-01-01',
            'gender': 'o',
            'register_id': other_register.id,
            'course_id': self.course.id,
            'application_date': '2026-07-01 10:00:00',
        })
        wizard = self._new_wizard(self.admission_linked | other_admission)
        service = self.env['irg.oficialidad.webhook.service']

        with patch.object(type(service), '_post_json', return_value=(200, '{}')):
            with self.assertRaises(UserError):
                wizard.action_send()

        self.assertFalse(self.admission_linked.oficialidad_sent_date)
        self.assertFalse(other_admission.oficialidad_sent_date)

    def test_default_get_rechaza_active_model_ajeno(self):
        wizard_model = self.env['oficialidad.send.wizard'].with_context(
            active_model='res.partner',
            active_id=self.register.id,
        )

        with self.assertRaises(UserError):
            wizard_model.default_get(['register_id', 'admission_ids'])

    def test_accion_y_boton_restringidos_a_administradores(self):
        group = self.env.ref(
            'openeducat_admission.group_op_admission_admin'
        )
        action = self.env.ref(
            'irg_admission_oficialidad_webhook.action_oficialidad_send_wizard'
        )
        button_view = self.env.ref(
            'irg_admission_oficialidad_webhook.'
            'view_op_admission_register_form_oficialidad'
        )

        self.assertEqual(action.groups_id, group)
        self.assertIn(
            'groups="openeducat_admission.group_op_admission_admin"',
            button_view.arch_db,
        )

    def test_urls_no_seguras_se_rechazan_antes_del_post(self):
        service = self.env['irg.oficialidad.webhook.service']
        invalid_urls = (
            'http://n8n.example.com/hook',
            'https://localhost/hook',
            'https://127.0.0.1/hook',
            'https://10.0.0.5/hook',
            'https://user:password@n8n.example.com/hook',
            'https://n8n.example.com/hook#fragment',
        )
        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                self.params.set_param(
                    'irg_oficialidad_webhook.webhook_url', invalid_url
                )
                with patch.object(type(service), '_post_json') as post_json:
                    with self.assertRaises(UserError):
                        service.send_oficialidad(
                            self.register, self.admission_linked
                        )
                post_json.assert_not_called()

    def test_hostname_resuelto_a_red_privada_se_rechaza(self):
        self.params.set_param(
            'irg_oficialidad_webhook.webhook_url',
            'https://n8n.example.com/hook',
        )
        service = self.env['irg.oficialidad.webhook.service']
        private_dns_result = [
            (2, 1, 6, '', ('192.168.10.5', 443)),
        ]

        with patch.object(
            service_module.socket,
            'getaddrinfo',
            return_value=private_dns_result,
        ), patch.object(type(service), '_post_json') as post_json:
            with self.assertRaises(UserError):
                service.send_oficialidad(self.register, self.admission_linked)

        post_json.assert_not_called()

    def test_hostname_resuelto_a_ip_publica_se_permite(self):
        self.params.set_param(
            'irg_oficialidad_webhook.webhook_url',
            'https://n8n.example.com/hook',
        )
        service = self.env['irg.oficialidad.webhook.service']
        public_dns_result = [
            (2, 1, 6, '', ('8.8.8.8', 443)),
        ]

        with patch.object(
            service_module.socket,
            'getaddrinfo',
            return_value=public_dns_result,
        ), patch.object(
            type(service), '_post_json', return_value=(200, '{}')
        ) as post_json:
            service.send_oficialidad(self.register, self.admission_linked)

        post_json.assert_called_once()

    def test_post_no_sigue_redirecciones(self):
        service = self.env['irg.oficialidad.webhook.service']
        redirect_error = url_error.HTTPError(
            'https://8.8.8.8/oficialidad',
            302,
            'Found',
            {},
            BytesIO(b'redirect body'),
        )
        opener = MagicMock()
        opener.open.side_effect = redirect_error
        legacy_response = MagicMock()
        legacy_response.__enter__.return_value = legacy_response
        legacy_response.read.return_value = b'redirect body'
        legacy_response.getcode.return_value = 302

        with patch.object(
            service_module.request,
            'build_opener',
            return_value=opener,
        ) as build_opener, patch.object(
            service_module.request,
            'urlopen',
            return_value=legacy_response,
        ):
            status, _body = service._post_json(
                'https://8.8.8.8/oficialidad', '{}', 'test-token', 15
            )

        self.assertEqual(status, 302)
        build_opener.assert_called_once()
        redirect_handler = next(
            handler for handler in build_opener.call_args.args
            if isinstance(
                handler, service_module.request.HTTPRedirectHandler
            )
        )
        self.assertIsInstance(
            redirect_handler, service_module.request.HTTPRedirectHandler
        )
        self.assertIsNone(
            redirect_handler.redirect_request(
                None, None, 302, 'Found', {}, 'https://1.1.1.1/other'
            )
        )

    def test_respuesta_http_limita_lectura_a_2001_bytes(self):
        service = self.env['irg.oficialidad.webhook.service']
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'x' * 2001
        response.getcode.return_value = 200
        opener = MagicMock()
        opener.open.return_value = response

        with patch.object(
            service_module.request,
            'build_opener',
            return_value=opener,
        ):
            status, body = service._post_json(
                'https://8.8.8.8/oficialidad', '{}', 'test-token', 15
            )

        self.assertEqual(status, 200)
        self.assertEqual(len(body), 2000)
        response.read.assert_called_once_with(2001)

    def test_conexion_https_usa_ip_pinnada_y_hostname_original(self):
        context = MagicMock()
        raw_socket = MagicMock()
        connection = service_module._PinnedHTTPSConnection(
            'n8n.example.com',
            pinned_ip='2001:4860:4860::8888',
            server_hostname='n8n.example.com',
            context=context,
        )
        connection._create_connection = MagicMock(return_value=raw_socket)

        connection.connect()

        connection._create_connection.assert_called_once_with(
            ('2001:4860:4860::8888', 443),
            connection.timeout,
            connection.source_address,
        )
        context.wrap_socket.assert_called_once_with(
            raw_socket,
            server_hostname='n8n.example.com',
        )

    def test_envio_entrega_ip_validada_sin_segunda_resolucion(self):
        self.params.set_param(
            'irg_oficialidad_webhook.webhook_url',
            'https://n8n.example.com/hook',
        )
        service = self.env['irg.oficialidad.webhook.service']
        public_dns_result = [(2, 1, 6, '', ('8.8.8.8', 443))]
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{}'
        response.getcode.return_value = 200
        opener = MagicMock()
        opener.open.return_value = response

        with patch.object(
            service_module.socket,
            'getaddrinfo',
            return_value=public_dns_result,
        ) as resolver, patch.object(
            service_module.request,
            'build_opener',
            return_value=opener,
        ) as build_opener:
            service.send_oficialidad(self.register, self.admission_linked)

        resolver.assert_called_once()
        pinned_handler = next(
            handler for handler in build_opener.call_args.args
            if isinstance(handler, service_module._PinnedHTTPSHandler)
        )
        self.assertEqual(pinned_handler.pinned_ip, '8.8.8.8')
        self.assertEqual(pinned_handler.server_hostname, 'n8n.example.com')

    def test_error_de_conexion_no_expone_detalle_interno(self):
        wizard = self._new_wizard(self.admission_linked)
        service = self.env['irg.oficialidad.webhook.service']
        internal_detail = (
            'Bearer super-secret https://n8n.example.com/hook?token=leak'
        )

        with patch.object(
            type(service), '_post_json', side_effect=RuntimeError(internal_detail)
        ):
            with self.assertRaises(UserError) as raised:
                wizard.action_send()

        message = str(raised.exception)
        self.assertNotIn('super-secret', message)
        self.assertNotIn('n8n.example.com', message)
        self.assertNotIn('token=leak', message)

    def test_error_http_no_expone_cuerpo_remoto(self):
        wizard = self._new_wizard(self.admission_linked)
        service = self.env['irg.oficialidad.webhook.service']
        remote_body = 'remote-secret-body'

        with patch.object(
            type(service), '_post_json', return_value=(500, remote_body)
        ):
            with self.assertRaises(UserError) as raised:
                wizard.action_send()

        message = str(raised.exception)
        self.assertIn('500', message)
        self.assertNotIn(remote_body, message)
