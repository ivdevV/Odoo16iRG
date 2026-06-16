# -*- coding: utf-8 -*-
import base64
from odoo.tests.common import HttpCase, tagged
from odoo.addons.mail.tests.common import mail_new_test_user


@tagged('post_install', '-at_install')
class TestCampusDiplomadosPortal(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Monkeypatch compute_final_subject_note en app.gradebook.subject
        cls._original_compute_final_subject_note = type(cls.env['app.gradebook.subject']).compute_final_subject_note
        
        def _mock_compute_final_subject_note(self):
            for rec in self:
                if rec.op_subject_id.code == 'SUBJOK':
                    rec.final_subject_note = 8.5
                elif rec.op_subject_id.code == 'SUBJFAIL':
                    rec.final_subject_note = 6.0
                else:
                    rec.final_subject_note = 0.0
                    
        type(cls.env['app.gradebook.subject']).compute_final_subject_note = _mock_compute_final_subject_note
        
        # Limpieza inicial
        leftover_users = cls.env['res.users'].sudo().search([('login', '=', 'student_portal_diplomados')])
        leftover_partners = leftover_users.partner_id
        
        leftover_so = cls.env['sale.order'].sudo().search([('partner_id', 'in', leftover_partners.ids)])
        if leftover_so:
            leftover_so.write({'state': 'draft'})
            leftover_so.unlink()

        cls.env['irg.diplomado.registry'].sudo().search([('name', 'in', ('TEST-DIP-01', 'TEST-DIP-02'))]).unlink()
        cls.env['app.gradebook.student'].sudo().search([('course_id.name', 'in', ('Diplomado Test 1', 'Diplomado Test 2', 'Master Test Normal'))]).unlink()
        cls.env['op.student'].sudo().search([('first_name', '=', 'PortalStudent')]).unlink()
        cls.env['op.admission'].sudo().search([('name', 'in', ('ADM-OK', 'ADM-FAIL', 'ADM-NORMAL'))]).unlink()
        cls.env['op.admission.register'].sudo().search([('name', 'in', ('Test Register OK', 'Test Register FAIL', 'Test Register Normal'))]).unlink()
        cls.env['op.subject'].sudo().search([('code', 'in', ('SUBJOK', 'SUBJFAIL'))]).unlink()
        cls.env['product.product'].sudo().search([('name', '=', 'Test Course Product Portal Dip')]).unlink()
        cls.env['op.batch'].sudo().search([('name', 'in', ('Batch OK', 'Batch FAIL', 'Batch Normal'))]).unlink()
        cls.env['op.course'].sudo().search([('name', 'in', ('Diplomado Test 1', 'Diplomado Test 2', 'Master Test Normal'))]).unlink()
        
        leftover_users.unlink()
        for partner in leftover_partners:
            try:
                partner.unlink()
            except Exception:
                pass
        cls.env.cr.commit()
        
        # Crear usuario del portal
        cls.portal_user = mail_new_test_user(
            cls.env,
            name='portal_student_diplomados',
            login='student_portal_diplomados',
            email='student_portal_diplomados@test.com',
            groups='base.group_portal',
        )
        
        # Estudiante
        cls.student = cls.env['op.student'].create({
            'partner_id': cls.portal_user.partner_id.id,
            'first_name': 'PortalStudent',
            'last_name': 'Diplomado',
        })
        
        # Cursos
        cls.course_ok = cls.env['op.course'].create({'name': 'Diplomado Test 1', 'code': 'DIP01'}) # Es diplomado (DI)
        cls.course_fail = cls.env['op.course'].create({'name': 'Diplomado Test 2', 'code': 'DIP02'}) # Es diplomado (DI)
        cls.course_normal = cls.env['op.course'].create({'name': 'Master Test Normal', 'code': 'MST01'}) # NO es diplomado

        # Lotes
        cls.batch_ok = cls.env['op.batch'].create({
            'name': 'Batch OK',
            'code': 'BOK',
            'course_id': cls.course_ok.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        cls.batch_fail = cls.env['op.batch'].create({
            'name': 'Batch FAIL',
            'code': 'BFAIL',
            'course_id': cls.course_fail.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        cls.batch_normal = cls.env['op.batch'].create({
            'name': 'Batch Normal',
            'code': 'BNORM',
            'course_id': cls.course_normal.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        
        # Producto y Registro
        cls.product = cls.env['product.product'].create({
            'name': 'Test Course Product Portal Dip',
            'type': 'service',
        })
        cls.register_ok = cls.env['op.admission.register'].create({
            'name': 'Test Register OK',
            'course_id': cls.course_ok.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.register_fail = cls.env['op.admission.register'].create({
            'name': 'Test Register FAIL',
            'course_id': cls.course_fail.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.register_normal = cls.env['op.admission.register'].create({
            'name': 'Test Register Normal',
            'course_id': cls.course_normal.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        
        # Admisiones
        cls.admission_ok = cls.env['op.admission'].create({
            'name': 'ADM-OK',
            'partner_id': cls.portal_user.partner_id.id,
            'student_id': cls.student.id,
            'course_id': cls.course_ok.id,
            'batch_id': cls.batch_ok.id,
            'register_id': cls.register_ok.id,
            'gender': 'm',
            'first_name': 'PortalStudent',
            'last_name': 'Diplomado',
        })
        cls.admission_fail = cls.env['op.admission'].create({
            'name': 'ADM-FAIL',
            'partner_id': cls.portal_user.partner_id.id,
            'student_id': cls.student.id,
            'course_id': cls.course_fail.id,
            'batch_id': cls.batch_fail.id,
            'register_id': cls.register_fail.id,
            'gender': 'm',
            'first_name': 'PortalStudent',
            'last_name': 'Diplomado',
        })
        cls.admission_normal = cls.env['op.admission'].create({
            'name': 'ADM-NORMAL',
            'partner_id': cls.portal_user.partner_id.id,
            'student_id': cls.student.id,
            'course_id': cls.course_normal.id,
            'batch_id': cls.batch_normal.id,
            'register_id': cls.register_normal.id,
            'gender': 'm',
            'first_name': 'PortalStudent',
            'last_name': 'Normal',
        })
        
        # Libretas académicas
        # Nota > 7 (ejemplo: 8.5)
        cls.gradebook_ok = cls.env['app.gradebook.student'].create({
            'partner_id': cls.portal_user.partner_id.id,
            'course_id': cls.course_ok.id,
            'batch_id': cls.batch_ok.id,
            'admission_id': cls.admission_ok.id,
            'state': 'done',
        })
        cls.op_subject_ok = cls.env['op.subject'].create({
            'name': 'Asignatura Ok',
            'code': 'SUBJOK',
            'course_id': cls.course_ok.id,
            'subject_type': 'compulsory',
        })
        cls.gradebook_subject_ok = cls.env['app.gradebook.subject'].create({
            'gradebook_student_id': cls.gradebook_ok.id,
            'op_subject_id': cls.op_subject_ok.id,
            'final_subject_note': 8.5,
        })
        cls.gradebook_ok._amount_prod_final()
        
        # Nota <= 7 (ejemplo: 6.0)
        cls.gradebook_fail = cls.env['app.gradebook.student'].create({
            'partner_id': cls.portal_user.partner_id.id,
            'course_id': cls.course_fail.id,
            'batch_id': cls.batch_fail.id,
            'admission_id': cls.admission_fail.id,
            'state': 'done',
        })
        cls.op_subject_fail = cls.env['op.subject'].create({
            'name': 'Asignatura Fail',
            'code': 'SUBJFAIL',
            'course_id': cls.course_fail.id,
            'subject_type': 'compulsory',
        })
        cls.gradebook_subject_fail = cls.env['app.gradebook.subject'].create({
            'gradebook_student_id': cls.gradebook_fail.id,
            'op_subject_id': cls.op_subject_fail.id,
            'final_subject_note': 6.0,
        })
        cls.gradebook_fail._amount_prod_final()

        # Libreta Normal (para Máster)
        cls.gradebook_normal = cls.env['app.gradebook.student'].create({
            'partner_id': cls.portal_user.partner_id.id,
            'course_id': cls.course_normal.id,
            'batch_id': cls.batch_normal.id,
            'admission_id': cls.admission_normal.id,
            'state': 'done',
        })
        
        # Crear adjunto de prueba simulado
        cls.test_attachment = cls.env['ir.attachment'].create({
            'name': 'diploma_test.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'PDF_TEST_CONTENT'),
            'mimetype': 'application/pdf',
        })
        
        # Crear los registros de diplomados
        cls.diplomado_ok = cls.env['irg.diplomado.registry'].create({
            'name': 'TEST-DIP-01',
            'student_id': cls.student.id,
            'student_name': 'PortalStudent Diplomado',
            'course_id': cls.course_ok.id,
            'diplomado_name': 'Diplomado Test 1',
            'issue_date': '2026-06-16',
            'diploma_type': 'digital',
            'attachment_id': cls.test_attachment.id,
        })
        
        cls.diplomado_fail = cls.env['irg.diplomado.registry'].create({
            'name': 'TEST-DIP-02',
            'student_id': cls.student.id,
            'student_name': 'PortalStudent Diplomado',
            'course_id': cls.course_fail.id,
            'diplomado_name': 'Diplomado Test 2',
            'issue_date': '2026-06-16',
            'diploma_type': 'digital',
            'attachment_id': cls.test_attachment.id,
        })
        
        # Crear orden de venta dummy para pasar controles académicos
        cls.env['sale.order'].sudo().create({
            'partner_id': cls.portal_user.partner_id.id,
            'state': 'sale',
        })
        
        cls.env.invalidate_all()
        cls.env.cr.commit()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, '_original_compute_final_subject_note'):
            type(cls.env['app.gradebook.subject']).compute_final_subject_note = cls._original_compute_final_subject_note
        cls.env.cr.rollback()
        super().tearDownClass()

    def test_01_diplomados_portal_list_and_download(self):
        # Autenticarse como usuario del portal
        self.authenticate('student_portal_diplomados', 'student_portal_diplomados')
        
        # 1. Comprobar que la página del portal carga correctamente
        response = self.url_open('/campus/certificates')
        self.assertEqual(response.status_code, 200, "La ruta del portal debe cargar correctamente.")
        html_content = response.text
        
        # 2. Comprobar que en la respuesta HTML se muestra el diplomado aprobado
        self.assertIn('TEST-DIP-01', html_content, "El diplomado con calificación > 7.0 debe estar visible en el portal.")
        # Y también el diplomado bloqueado con la insignia correspondiente
        self.assertIn('TEST-DIP-02', html_content, "El diplomado con calificación <= 7.0 debe estar visible en el portal.")
        self.assertIn('Bloqueado', html_content, "Debe mostrarse la indicación de bloqueo.")
        self.assertIn('Mis Diplomados', html_content, "La pestaña independiente 'Mis Diplomados' debe estar visible.")
        
        # 3. Descarga del diplomado Ok (debe dar 200 y descargar el PDF)
        download_ok_url = f'/campus/certificates/download/diplomado/{self.diplomado_ok.id}'
        response_download = self.url_open(download_ok_url)
        self.assertEqual(response_download.status_code, 200, "La descarga del diplomado aprobado debe retornar 200.")
        self.assertEqual(response_download.content, b'PDF_TEST_CONTENT', "El contenido descargado debe coincidir con el PDF del diplomado.")
        
        # 4. Descarga del diplomado Bloqueado (debe redirigir a /campus/certificates con error=grade_too_low)
        download_fail_url = f'/campus/certificates/download/diplomado/{self.diplomado_fail.id}'
        response_fail = self.url_open(download_fail_url)
        self.assertEqual(response_fail.status_code, 200, "La llamada debe completarse con redirección (código HTTP final 200 al renderizar el portal).")
        self.assertIn('error=grade_too_low', response_fail.url, "La redirección debe incluir el parámetro de error de calificación baja.")

    def test_02_diplomados_request_form_exclusion(self):
        # Autenticarse como usuario del portal
        self.authenticate('student_portal_diplomados', 'student_portal_diplomados')

        # 1. Acceder al formulario de nueva solicitud de certificados
        response = self.url_open('/campus/certificates/new')
        self.assertEqual(response.status_code, 200)
        html_content = response.text

        # 2. Comprobar que en el dropdown de programas académicos NO aparecen los diplomados, pero sí el máster normal
        self.assertIn('Master Test Normal', html_content, "El curso Máster Normal debe figurar en el desplegable de solicitudes.")
        self.assertNotIn('Diplomado Test 1', html_content, "El Diplomado Test 1 debe estar excluido por completo del desplegable de solicitudes.")
        self.assertNotIn('Diplomado Test 2', html_content, "El Diplomado Test 2 debe estar excluido por completo del desplegable de solicitudes.")

        # 3. Intentar enviar una solicitud POST con el ID del diplomado (debe fallar devolviendo error)
        # Extraer el CSRF token de la respuesta GET anterior
        import re
        csrf_token = None
        csrf_js = re.search(r'csrf_token:\s*["\']([^"\']+)["\']', html_content)
        if csrf_js:
            csrf_token = csrf_js.group(1)
        else:
            csrf_input = re.search(r'name="csrf_token"\s+value="([^"]+)"', html_content)
            if csrf_input:
                csrf_token = csrf_input.group(1)

        # Enviamos datos para solicitar el diploma para la libreta del diplomado
        post_data = {
            'document_type': 'diploma',
            'certificate_type': 'digital',
            'gradebook_id': str(self.gradebook_ok.id),
        }
        if csrf_token:
            post_data['csrf_token'] = csrf_token

        # Hacemos la llamada POST
        response_post = self.url_open('/campus/certificates/new', data=post_data)
        # El controlador interceptará la libreta del diplomado, la forzará a '0' y el padre devolverá error en el HTML
        self.assertEqual(response_post.status_code, 200)
        self.assertIn('Selecciona la libreta', response_post.text, "El controlador debe rechazar y solicitar seleccionar una libreta válida (ya que forzamos a 0).")
