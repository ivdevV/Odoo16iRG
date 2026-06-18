# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock


class TestCampusWorkshops(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCampusWorkshops, cls).setUpClass()
        # Crear producto para admisión
        cls.product = cls.env['product.product'].create({
            'name': 'Test Admission Product',
            'type': 'service',
        })

    def test_view_inheritance(self):
        """Verifica que la vista herede de forma correcta y contenga la sección Talleres y la tarjeta iRG Empower."""
        # Obtener la vista heredada por su external ID
        view = self.env.ref('irg_campus_workshops.irg_user_profile_content_workshops')
        self.assertTrue(view.active, "La vista heredada de talleres debe estar activa.")

        # Verificar que el arch de la vista heredada contiene la sección
        arch = view.arch
        self.assertIn('Talleres', arch, "La vista debe definir la sección Talleres.")
        self.assertIn('https://app.institutoraimongaja.com/slides/irg-empower-261', arch, "La tarjeta debe apuntar a la URL de redirección específica.")
        self.assertIn('irg_empower_logo.jpg', arch, "La tarjeta debe incluir la imagen del logo.")

    def test_auto_enrollment(self):
        """Verifica que un usuario autenticado sea auto-inscrito automáticamente al acceder al canal de iRG Empower."""
        # 1. Crear un canal de prueba que contenga 'empower' en el nombre
        channel = self.env['slide.channel'].create({
            'name': 'iRG Empower Test Channel',
            'enroll': 'public',
            'visibility': 'public',
        })

        # 2. Crear un partner y usuario de prueba (no inscrito)
        partner = self.env['res.partner'].create({'name': 'Student Test Partner'})
        user = self.env['res.users'].create({
            'name': 'Student Test User',
            'login': 'student_test_user_workshops',
            'partner_id': partner.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # 3. Comprobar que no hay registro de inscripción
        domain = [('partner_id', '=', partner.id), ('channel_id', '=', channel.id)]
        self.assertEqual(self.env['slide.channel.partner'].search_count(domain), 0)

        # 4. Instanciar el controlador
        from odoo.addons.irg_campus_workshops.controllers.main import WebsiteSlidesWorkshops
        controller = WebsiteSlidesWorkshops()

        # Mockear request de odoo.http
        mock_request = MagicMock()
        mock_request.env = self.env(user=user)
        mock_request.website = self.env['website'].browse(1)

        # Reemplazar el request local en el archivo main.py del controlador
        with patch('odoo.addons.irg_campus_workshops.controllers.main.request', mock_request):
            try:
                controller.channel(channel)
            except Exception:
                # El render final de super().channel() puede fallar/lanzar excepciones si el entorno mockeado
                # carece de request completo, pero la lógica de inscripción en el método sobreescrito se ejecuta primero.
                pass

        # 5. Verificar que se ha creado la inscripción automática
        self.assertEqual(self.env['slide.channel.partner'].search_count(domain), 1,
                         "El alumno de prueba debería haber sido auto-inscrito en el canal al acceder al mismo.")

    def _create_mock_request(self, user):
        from unittest.mock import MagicMock
        class SessionMock(dict):
            def __getattr__(self, name):
                if name in self:
                    return self[name]
                return None

        session = SessionMock()
        session['force_website_id'] = 1
        session['debug'] = ""
        session['context'] = {'lang': 'es_ES'}
        session.geoip = {}
        session.debug = ""
        session.context = {'lang': 'es_ES'}

        mock_request = MagicMock()
        mock_request.params = {}
        mock_request.session = session
        mock_request.context = {'lang': 'es_ES'}
        mock_request.env = self.env(user=user)
        mock_request.website = self.env['website'].browse(1)
        mock_request.registry = self.env.registry
        mock_request.httprequest = MagicMock()
        mock_request.httprequest.args = {}
        mock_request.httprequest.form = {}
        mock_request.httprequest.cookies = {}
        mock_request.httprequest.environ = {'installed_modules': ['website']}
        mock_request.httprequest.url = "http://localhost:8069"
        mock_request.httprequest.path = "/campus"
        return mock_request

    def test_workshops_visibility_only_diplomado(self):
        """Verifica que la sección de talleres se oculte si el alumno está inscrito ÚNICAMENTE en diplomados."""
        from odoo.http import _request_stack
        # 1. Crear tipo de curso diplomado y curso diplomado
        type_diplomado = self.env['op.course.type'].create({
            'name': 'DIPLOMADO DE PRUEBA',
            'code': 'DI',
        })
        course_diplomado = self.env['op.course'].create({
            'name': 'Diplomado Test Course',
            'code': 'DI-TEST',
            'course_type_id': type_diplomado.id,
        })
        
        # 2. Crear un curso máster (no diplomado)
        type_master = self.env['op.course.type'].create({
            'name': 'MÁSTER DE PRUEBA',
            'code': 'M',
        })
        course_master = self.env['op.course'].create({
            'name': 'Master Test Course',
            'code': 'M-TEST',
            'course_type_id': type_master.id,
        })

        # 3. Crear registros de admisión (admission register) requeridos por NotNull
        register_diplomado = self.env['op.admission.register'].create({
            'name': 'Register Diplomado Test',
            'course_id': course_diplomado.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })
        register_master = self.env['op.admission.register'].create({
            'name': 'Register Master Test',
            'course_id': course_master.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })

        # 4. Crear un partner, usuario y op.student de prueba
        partner = self.env['res.partner'].create({'name': 'Student Visibility Partner'})
        user = self.env['res.users'].create({
            'name': 'Student Visibility User',
            'login': 'student_visibility_user_workshops',
            'partner_id': partner.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Visibility',
            'last_name': 'Student',
        })

        # 5. Caso 1: Estudiante inscrito únicamente en el curso Diplomado
        self.env['op.admission'].create({
            'name': 'ADM-DIPLOMADO-ONLY',
            'partner_id': partner.id,
            'course_id': course_diplomado.id,
            'register_id': register_diplomado.id,
            'state': 'done',
            'gender': 'm',
            'first_name': 'Visibility',
            'last_name': 'Student',
        })

        view = self.env.ref('isep_website_custom.user_profile_content')
        
        # Renderizar como el usuario autenticado (sólo inscrito en Diplomado)
        mock_request = self._create_mock_request(user)
        _request_stack.push(mock_request)
        try:
            html = self.env['ir.qweb'].with_user(user)._render('isep_website_custom.user_profile_content', {
                'user': user,
                'env': self.env(user=user),
                'channel': True,
                'website': self.env['website'].browse(1),
            })
            # No debe aparecer el título "Talleres" ni la tarjeta irg_empower_logo.jpg
            self.assertNotIn('Talleres', str(html), "La sección Talleres debería estar oculta para alumnos inscritos únicamente en Diplomados.")
            self.assertNotIn('irg_empower_logo.jpg', str(html))
        finally:
            _request_stack.pop()

        # 6. Caso 2: Estudiante inscrito también en un Máster
        self.env['op.admission'].create({
            'name': 'ADM-MASTER-ALSO',
            'partner_id': partner.id,
            'course_id': course_master.id,
            'register_id': register_master.id,
            'state': 'done',
            'gender': 'm',
            'first_name': 'Visibility',
            'last_name': 'Student',
        })

        # Renderizar de nuevo
        mock_request = self._create_mock_request(user)
        _request_stack.push(mock_request)
        try:
            html = self.env['ir.qweb'].with_user(user)._render('isep_website_custom.user_profile_content', {
                'user': user,
                'env': self.env(user=user),
                'channel': True,
                'website': self.env['website'].browse(1),
            })
            # Debe aparecer la sección "Talleres" porque ya no está inscrito "únicamente" en Diplomados
            self.assertIn('Talleres', str(html), "La sección Talleres debería mostrarse si el alumno está inscrito en al menos un curso que no es Diplomado.")
            self.assertIn('irg_empower_logo.jpg', str(html))
        finally:
            _request_stack.pop()

