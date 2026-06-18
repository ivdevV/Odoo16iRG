# -*- coding: utf-8 -*-
import base64
from odoo.tests.common import HttpCase, tagged
from odoo.addons.mail.tests.common import mail_new_test_user


@tagged('post_install', '-at_install')
class TestCampusCertificatesPortal(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Clean up any leftover records from previously aborted runs to prevent duplicate key/login errors
        leftover_users = cls.env['res.users'].sudo().search([('login', 'in', ('student_portal_certificates', 'other_student'))])
        leftover_partners = leftover_users.partner_id
        
        leftover_so = cls.env['sale.order'].sudo().search([('partner_id', 'in', leftover_partners.ids)])
        if leftover_so:
            leftover_so.write({'state': 'draft'})
            leftover_so.unlink()
        
        if 'op.session' in cls.env:
            cls.env['op.session'].sudo().search([('name', '=', 'Test Session')]).unlink()
            cls.env['op.session'].sudo().search([('subject_id.code', 'in', ('TS01', 'TSPORTAL'))]).unlink()
        if 'op.faculty' in cls.env:
            cls.env['op.faculty'].sudo().search([('name', '=', 'Faculty Test')]).unlink()
        cls.env['op.subject'].sudo().search([('code', 'in', ('TS01', 'TSPORTAL'))]).unlink()
        cls.env['irg.certificate.request'].sudo().search([('gradebook_student_id.course_id.name', 'in', ('Test Course Portal', 'Test Course Portal Done'))]).unlink()
        cls.env['app.gradebook.student'].sudo().search([('course_id.name', 'in', ('Test Course Portal', 'Test Course Portal Done'))]).unlink()
        cls.env['irg.tfm.acta'].sudo().search([('degree_name', '=', 'Máster de Prueba')]).unlink()
        cls.env['irg.diploma.registry'].sudo().search([('registry_number', '=', 'TEST-DIPLOMA-01')]).unlink()
        cls.env['ir.attachment'].sudo().search([('name', '=', 'test_cert.pdf')]).unlink()
        cls.env['op.admission'].sudo().search([('name', 'in', ('ADM-TEST-PORTAL', 'ADM-TEST-PORTAL-DONE'))]).unlink()
        cls.env['op.admission.register'].sudo().search([('name', 'in', ('Test Register Portal', 'Test Register Portal Done'))]).unlink()
        cls.env['product.product'].sudo().search([('name', '=', 'Test Course Product Portal')]).unlink()
        cls.env['op.batch'].sudo().search([('name', 'in', ('Batch Portal HC', 'Batch Portal Done'))]).unlink()
        cls.env['op.course'].sudo().search([('name', 'in', ('Test Course Portal', 'Test Course Portal Done'))]).unlink()
        cls.env['op.student'].sudo().search([('first_name', 'in', ('Test', 'Other')), ('last_name', '=', 'Student')]).unlink()
        
        leftover_users.unlink()
        for partner in leftover_partners:
            try:
                partner.unlink()
            except Exception:
                pass
        cls.env.cr.commit()

        # Create a portal user
        cls.portal_user = mail_new_test_user(
            cls.env,
            name='portal_student_certificates',
            login='student_portal_certificates',
            email='student_portal_certificates@test.com',
            groups='base.group_portal',
        )
        
        # Associate partner with student
        cls.student = cls.env['op.student'].create({
            'partner_id': cls.portal_user.partner_id.id,
            'first_name': 'Test',
            'last_name': 'Student',
        })
        
        # Create course and batch for gradebook
        cls.course = cls.env['op.course'].create({'name': 'Test Course Portal', 'code': 'TCP01'})
        cls.batch = cls.env['op.batch'].create({
            'name': 'Batch Portal HC',
            'code': 'BPHC',
            'course_id': cls.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Course Product Portal',
            'type': 'service',
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'Test Register Portal',
            'course_id': cls.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.admission = cls.env['op.admission'].create({
            'name': 'ADM-TEST-PORTAL',
            'partner_id': cls.portal_user.partner_id.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'register_id': cls.register.id,
            'gender': 'm',
            'first_name': 'Test',
            'last_name': 'Student',
        })
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.portal_user.partner_id.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
            'state': 'in_progress',
        })
        
        # Create a session to use for attendance certificate tests
        if 'op.session' in cls.env:
            faculty = cls.env['op.faculty'].create({
                'name': 'Faculty Test',
                'first_name': 'Faculty',
                'last_name': 'Test',
                'birth_date': '2000-01-01',
                'gender': 'male',
            })
            subject = cls.env['op.subject'].create({
                'name': 'Test Subject',
                'code': 'TSPORTAL',
                'course_id': cls.course.id,
            })
            cls.op_session = cls.env['op.session'].create({
                'name': 'Test Session',
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'subject_id': subject.id,
                'start_datetime': '2026-06-03 10:00:00',
                'end_datetime': '2026-06-03 11:00:00',
                'state': 'confirm',
                'faculty_id': faculty.id,
            })
        
        # Create second course and batch for gradebook_done
        cls.course_done = cls.env['op.course'].create({'name': 'Test Course Portal Done', 'code': 'TCP02'})
        cls.batch_done = cls.env['op.batch'].create({
            'name': 'Batch Portal Done',
            'code': 'BPD',
            'course_id': cls.course_done.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        cls.register_done = cls.env['op.admission.register'].create({
            'name': 'Test Register Portal Done',
            'course_id': cls.course_done.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.admission_done = cls.env['op.admission'].create({
            'name': 'ADM-TEST-PORTAL-DONE',
            'partner_id': cls.portal_user.partner_id.id,
            'course_id': cls.course_done.id,
            'batch_id': cls.batch_done.id,
            'register_id': cls.register_done.id,
            'gender': 'm',
            'first_name': 'Test',
            'last_name': 'Student',
        })
        cls.gradebook_done = cls.env['app.gradebook.student'].create({
            'partner_id': cls.portal_user.partner_id.id,
            'course_id': cls.course_done.id,
            'batch_id': cls.batch_done.id,
            'admission_id': cls.admission_done.id,
            'state': 'done',
        })
        
        # Create an attachment to use for testing
        cls.attachment = cls.env['ir.attachment'].create({
            'name': 'test_cert.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'PDF CONTENT'),
            'res_model': 'op.student',
            'res_id': cls.student.id,
        })
        
        # Create a valid diploma registry
        cls.diploma = cls.env['irg.diploma.registry'].create({
            'registry_number': 'TEST-DIPLOMA-01',
            'student_id': cls.student.id,
            'issue_date': '2026-05-24',
            'diploma_type': 'digital',
            'attachment_id': cls.attachment.id,
            'state': 'valid',
        })
        
        # Create an acta
        cls.acta = cls.env['irg.tfm.acta'].create({
            'student_id': cls.student.id,
            'student_name': 'Test',
            'student_surnames': 'Student',
            'academic_year': '2025-2026',
            'degree_name': 'Máster de Prueba',
            'tfm_title': 'Título TFM Prueba',
            'director_name': 'Dir',
            'director_surnames': 'D',
            'president_name': 'Pres',
            'president_surnames': 'P',
            'secretary_name': 'Sec',
            'secretary_surnames': 'S',
            'acta_type': 'tfm',
            'apto_status': 'apto',
            'defense_date': '2026-05-24',
            'attachment_id': cls.attachment.id,
            'state': 'valid',
        })
        # Create another user and student
        cls.other_user = mail_new_test_user(
            cls.env,
            name='other_student',
            login='other_student',
            email='other_student@test.com',
            groups='base.group_portal',
        )
        cls.other_student = cls.env['op.student'].create({
            'partner_id': cls.other_user.partner_id.id,
            'first_name': 'Other',
            'last_name': 'Student',
        })
        
        # Configure and enable Stripe Payment Provider
        cls.stripe_provider = cls.env['payment.provider'].sudo().search([('code', '=', 'stripe')], limit=1)
        if not cls.stripe_provider:
            cls.stripe_provider = cls.env['payment.provider'].sudo().create({
                'name': 'Stripe Test',
                'code': 'stripe',
                'state': 'test',
                'is_published': True,
                'stripe_publishable_key': 'pk_test_dummy',
                'stripe_secret_key': 'sk_test_dummy',
                'stripe_webhook_secret': 'whsec_test_dummy',
            })
        else:
            cls.stripe_provider.write({
                'state': 'test',
                'is_published': True,
                'stripe_publishable_key': 'pk_test_dummy',
                'stripe_secret_key': 'sk_test_dummy',
                'stripe_webhook_secret': 'whsec_test_dummy',
            })
            
        # Create dummy sale orders to pass academic checks
        cls.env['sale.order'].sudo().create({
            'partner_id': cls.portal_user.partner_id.id,
            'state': 'sale',
        })
        cls.env['sale.order'].sudo().create({
            'partner_id': cls.other_user.partner_id.id,
            'state': 'sale',
        })
            
        # Monkeypatch _stripe_make_request directly on the registry model class
        cls._original_stripe_make_request = type(cls.env['payment.provider'])._stripe_make_request
        
        def _mock_stripe_make_request_bound(self, endpoint, payload=None, method='POST', offline=False, idempotency_key=None, **kwargs):
            print("MONKEYPATCH MOCK STRIPE CALLED: endpoint=%s, method=%s, payload=%s" % (endpoint, method, payload))
            if "checkout/sessions" in endpoint:
                return {
                    'id': 'cs_test_12345',
                    'url': 'https://checkout.stripe.com/pay/cs_test_12345',
                    'payment_status': 'paid',
                }
            elif "invoices/" in endpoint:
                return {
                    'hosted_invoice_url': 'https://stripe.com/invoice/hosted',
                    'invoice_pdf': 'https://stripe.com/invoice/pdf',
                }
            elif "payment_intents/" in endpoint:
                return {
                    'charges': {
                        'data': [
                            {'receipt_url': 'https://stripe.com/receipt'}
                        ]
                    }
                }
            elif "customers" in endpoint:
                return {
                    'id': 'cus_test_12345',
                }
            return {}

        type(cls.env['payment.provider'])._stripe_make_request = _mock_stripe_make_request_bound
        
        cls.env.cr.commit()

    @classmethod
    def tearDownClass(cls):
        # Restore _stripe_make_request on the registry model class
        if hasattr(cls, '_original_stripe_make_request'):
            type(cls.env['payment.provider'])._stripe_make_request = cls._original_stripe_make_request
            
        # Rollback local transaction to start a fresh one and see HTTP thread commits
        cls.env.cr.rollback()

        # Disable stripe provider
        if hasattr(cls, 'stripe_provider') and cls.stripe_provider:
            cls.stripe_provider.write({'state': 'disabled'})

        # Clean up sale orders first
        leftover_so = cls.env['sale.order'].sudo().search([('partner_id', 'in', (cls.portal_user.partner_id.id, cls.other_user.partner_id.id))])
        if leftover_so:
            leftover_so.write({'state': 'draft'})
            leftover_so.unlink()

        # Clean up records from DB
        if 'op.session' in cls.env:
            cls.env['op.session'].sudo().search([('name', '=', 'Test Session')]).unlink()
            cls.env['op.session'].sudo().search([('subject_id.code', 'in', ('TS01', 'TSPORTAL'))]).unlink()
        if 'op.faculty' in cls.env:
            cls.env['op.faculty'].sudo().search([('name', '=', 'Faculty Test')]).unlink()
        cls.env['op.subject'].sudo().search([('code', 'in', ('TS01', 'TSPORTAL'))]).unlink()
        cls.env['irg.tfm.acta'].sudo().search([('degree_name', '=', 'Máster de Prueba')]).unlink()
        cls.env['irg.diploma.registry'].sudo().search([('registry_number', '=', 'TEST-DIPLOMA-01')]).unlink()
        cls.env['ir.attachment'].sudo().search([('name', '=', 'test_cert.pdf')]).unlink()
        
        cls.env['irg.certificate.request'].sudo().search([
            '|',
            ('partner_id', '=', cls.portal_user.partner_id.id),
            ('gradebook_student_id', 'in', [cls.gradebook.id, cls.gradebook_done.id])
        ]).unlink()

        cls.env['app.gradebook.student'].sudo().search([('partner_id', '=', cls.portal_user.partner_id.id)]).unlink()
        cls.env['op.admission'].sudo().search([('name', 'in', ('ADM-TEST-PORTAL', 'ADM-TEST-PORTAL-DONE'))]).unlink()
        cls.env['op.admission.register'].sudo().search([('name', 'in', ('Test Register Portal', 'Test Register Portal Done'))]).unlink()
        cls.env['product.product'].sudo().search([('name', '=', 'Test Course Product Portal')]).unlink()
        cls.env['op.batch'].sudo().search([('name', 'in', ('Batch Portal HC', 'Batch Portal Done'))]).unlink()
        cls.env['op.course'].sudo().search([('name', 'in', ('Test Course Portal', 'Test Course Portal Done'))]).unlink()

        cls.env['op.student'].sudo().search([('first_name', 'in', ('Test', 'Other')), ('last_name', '=', 'Student')]).unlink()
        
        users = cls.env['res.users'].sudo().search([('login', 'in', ('student_portal_certificates', 'other_student'))])
        partners = users.partner_id
        users.unlink()
        for partner in partners:
            try:
                partner.unlink()
            except Exception:
                pass
        
        cls.env.cr.commit()
        super().tearDownClass()

    @staticmethod
    def _mock_stripe_make_request(*args, **kwargs):
        print("MOCK STRIPE CALLED: args=%s, kwargs=%s" % (str(args), str(kwargs)))
        endpoint = args[1] if len(args) > 1 else kwargs.get('endpoint', '')
        if not isinstance(endpoint, str):
            for arg in args:
                if isinstance(arg, str):
                    endpoint = arg
                    break
        if "checkout/sessions" in endpoint:
            return {
                'id': 'cs_test_12345',
                'url': 'https://checkout.stripe.com/pay/cs_test_12345',
                'payment_status': 'paid',
            }
        elif "invoices/" in endpoint:
            return {
                'hosted_invoice_url': 'https://stripe.com/invoice/hosted',
                'invoice_pdf': 'https://stripe.com/invoice/pdf',
            }
        elif "payment_intents/" in endpoint:
            return {
                'charges': {
                    'data': [
                        {'receipt_url': 'https://stripe.com/receipt'}
                    ]
                }
            }
        elif "customers" in endpoint:
            return {
                'id': 'cus_test_12345',
            }
        return {}

    def test_01_campus_certificates_unauthorized_redirects(self):
        """Unauthenticated requests should be redirected to login page."""
        self.authenticate(None, None)
        response = self.url_open('/campus/certificates')
        # Check redirection to login
        self.assertTrue('/web/login' in response.url or response.status_code in (301, 302, 401, 403), 
                        'Unauthorized user was not redirected or blocked.')

    def test_02_campus_certificates_authorized_success(self):
        """Authenticated portal user should load the certificates dashboard successfully."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open('/campus/certificates')
        self.assertEqual(response.status_code, 200, 'Could not access certificates portal.')
        # Check that our diploma and acta are in the response HTML body
        self.assertIn('TEST-DIPLOMA-01', response.text)
        self.assertIn('Título TFM Prueba', response.text)

    def test_03_download_diploma_and_acta(self):
        """Authenticated student should be able to download their diploma and acta."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        
        # Download diploma
        diploma_url = f"/campus/certificates/download/diploma/{self.diploma.id}"
        response_dip = self.url_open(diploma_url)
        self.assertEqual(response_dip.status_code, 200)
        self.assertEqual(response_dip.content, b'PDF CONTENT')
        
        # Download acta
        acta_url = f"/campus/certificates/download/acta/{self.acta.id}"
        response_acta = self.url_open(acta_url)
        self.assertEqual(response_acta.status_code, 200)
        self.assertEqual(response_acta.content, b'PDF CONTENT')

    def test_04_download_other_student_document_fails(self):
        """A student should not be able to download another student's diploma or acta."""
        self.authenticate(self.other_user.login, self.other_user.login)
        
        # Attempt downloading original student's diploma
        diploma_url = f"/campus/certificates/download/diploma/{self.diploma.id}"
        response_dip = self.url_open(diploma_url)
        # Should redirect back to dashboard list
        self.assertTrue('/campus/certificates' in response_dip.url)
        
        # Attempt downloading original student's acta
        acta_url = f"/campus/certificates/download/acta/{self.acta.id}"
        response_acta = self.url_open(acta_url)
        # Should redirect back to dashboard list
        self.assertTrue('/campus/certificates' in response_acta.url)

    def test_05_portal_new_certificate_get_preselection(self):
        """Test GET /campus/certificates/new with and without course_id preselection."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        
        # 1. Without course_id
        response = self.url_open('/campus/certificates/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Tipo de Certificación', response.text)
        
        # Check that the new document type options are present in the response
        self.assertIn('value="gradebook"', response.text)
        self.assertIn('value="gradebook_partial"', response.text)
        self.assertIn('value="diploma"', response.text)
        self.assertIn('value="attendance"', response.text)
        self.assertIn('value="enrollment"', response.text)
        
        # 2. With course_id matching our gradebook's course
        course_url = f'/campus/certificates/new?course_id={self.course.id}'
        response_course = self.url_open(course_url)
        self.assertEqual(response_course.status_code, 200)
        # Check that the option for our gradebook has the selected attribute
        self.assertIn(f'value="{self.gradebook.id}"', response_course.text)
        self.assertIn('selected="selected"', response_course.text)

    def test_06_portal_new_certificate_post_validation(self):
        """Test POST /campus/certificates/new with different document types and states."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        
        import re
        response_get = self.url_open('/campus/certificates/new')
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response_get.text)
        csrf_token = match.group(1) if match else ''
        
        # 1. Requesting 'gradebook' (complete) on an in-progress gradebook should fail
        post_data = {
            'csrf_token': csrf_token,
            'document_type': 'gradebook',
            'certificate_type': 'digital',
            'gradebook_id': str(self.gradebook.id),
            'signer': 'raimon',
        }
        response_post1 = self.url_open('/campus/certificates/new', data=post_data)
        self.assertEqual(response_post1.status_code, 200)
        self.assertIn('tu libreta debe estar finalizada', response_post1.text)

        # 1b. Requesting 'diploma' on an in-progress gradebook should also fail
        post_data['document_type'] = 'diploma'
        response_post_dip_fail = self.url_open('/campus/certificates/new', data=post_data)
        self.assertEqual(response_post_dip_fail.status_code, 200)
        self.assertIn('tu libreta debe estar finalizada', response_post_dip_fail.text)

        # 2. Requesting 'gradebook_partial' (partial) on an in-progress gradebook should succeed
        post_data['document_type'] = 'gradebook_partial'
        response_post2 = self.url_open('/campus/certificates/new', data=post_data, allow_redirects=False)
        if response_post2.status_code not in (302, 303):
            print("DEBUG: response_post2.status_code is %s" % response_post2.status_code)
            print("DEBUG: response_post2.text is:\n%s" % response_post2.text)
        self.assertIn(response_post2.status_code, (302, 303))
        self.assertIn('checkout.stripe.com', response_post2.headers.get('Location', ''))

        # 3. Requesting 'attendance' on an in-progress gradebook should succeed
        post_data['document_type'] = 'attendance'
        if hasattr(self, 'op_session'):
            post_data['session_id'] = str(self.op_session.id)
        response_post3 = self.url_open('/campus/certificates/new', data=post_data, allow_redirects=False)
        self.assertIn(response_post3.status_code, (302, 303))
        if 'session_id' in self.env['irg.certificate.request']._fields:
            self.assertIn('/campus/certificates/confirm/', response_post3.headers.get('Location', ''))
        else:
            self.assertIn('checkout.stripe.com', response_post3.headers.get('Location', ''))

        # 4. Requesting 'enrollment' on an in-progress gradebook should succeed
        post_data['document_type'] = 'enrollment'
        response_post4 = self.url_open('/campus/certificates/new', data=post_data, allow_redirects=False)
        if response_post4.status_code not in (302, 303):
            print("DEBUG ENROLLMENT: status=%s body=%s" % (response_post4.status_code, response_post4.text))
        self.assertIn(response_post4.status_code, (302, 303))
        self.assertIn('checkout.stripe.com', response_post4.headers.get('Location', ''))

        # 5. Requesting 'gradebook' on a finished gradebook should succeed
        post_data['gradebook_id'] = str(self.gradebook_done.id)
        post_data['document_type'] = 'gradebook'
        response_post5 = self.url_open('/campus/certificates/new', data=post_data, allow_redirects=False)
        self.assertIn(response_post5.status_code, (302, 303))
        self.assertIn('checkout.stripe.com', response_post5.headers.get('Location', ''))

        # Requesting 'diploma' on a finished gradebook should succeed
        post_data['document_type'] = 'diploma'
        response_post6 = self.url_open('/campus/certificates/new', data=post_data, allow_redirects=False)
        self.assertIn(response_post6.status_code, (302, 303))
        self.assertIn('checkout.stripe.com', response_post6.headers.get('Location', ''))

    def test_07_stripe_webhook_completed_sync(self):
        """Simulate reception of checkout.session.completed webhook via stripe.sync."""
        # 1. Crear una solicitud de certificado que esté pendiente de pago
        cert_req = self.env['irg.certificate.request'].sudo().create({
            'gradebook_student_id': self.gradebook_done.id,
            'document_type': 'diploma',
            'certificate_type': 'digital',
            'signer': 'raimon',
            'state': 'pending_payment',
            'origin': 'portal',
        })
        
        # 2. Generar el payload simulado que envía Stripe
        session_payload = {
            'id': 'cs_test_webhook_123',
            'object': 'checkout.session',
            'amount_total': 1500,  # 15.00 EUR
            'currency': 'eur',
            'customer': 'cus_test_webhook',
            'payment_status': 'paid',
            'payment_intent': 'pi_test_webhook',
            'invoice': 'in_test_webhook',
            'metadata': {
                'certificate_request_id': str(cert_req.id),
            }
        }
        
        # 3. Invocar al método de stripe.sync
        self.env['stripe.sync']._sync_checkout_session(session_payload)
        
        # 4. Verificar el cambio de estados
        cert_req.invalidate_model(['state', 'stripe_payment_status', 'attachment_id', 'diploma_registry_id'])
        self.assertEqual(cert_req.state, 'done')
        self.assertEqual(cert_req.stripe_payment_status, 'paid')
        self.assertEqual(cert_req.stripe_checkout_session_id, 'cs_test_webhook_123')
        self.assertEqual(cert_req.stripe_payment_intent_id, 'pi_test_webhook')
        self.assertEqual(cert_req.stripe_invoice_id, 'in_test_webhook')
        
        # 5. Verificar vinculación del attachment de PDF al diploma registry
        self.assertTrue(cert_req.attachment_id, "Debería haberse generado un PDF adjunto.")
        
        diploma = cert_req.diploma_registry_id
        self.assertTrue(diploma.exists(), "Debería haberse vinculado a un registro de diploma.")
        self.assertEqual(diploma.attachment_id, cert_req.attachment_id, "El adjunto del diploma debería ser el mismo que el del certificado.")
        self.assertEqual(diploma.state, 'valid', "El diploma debería estar en estado válido.")

        # Testear para certificado físico (debe quedar en in_process)
        cert_physical = self.env['irg.certificate.request'].sudo().create({
            'gradebook_student_id': self.gradebook_done.id,
            'document_type': 'gradebook',
            'certificate_type': 'physical',
            'shipping_type': 'national',
            'signer': 'raimon',
            'state': 'pending_payment',
            'origin': 'portal',
        })
        
        physical_payload = {
            'id': 'cs_test_webhook_physical',
            'object': 'checkout.session',
            'amount_total': 3000,
            'currency': 'eur',
            'customer': 'cus_test_webhook',
            'payment_status': 'paid',
            'payment_intent': 'pi_test_webhook_phys',
            'invoice': 'in_test_webhook_phys',
            'metadata': {
                'certificate_request_id': str(cert_physical.id),
            }
        }
        self.env['stripe.sync']._sync_checkout_session(physical_payload)
        cert_physical.invalidate_model(['state'])
        self.assertEqual(cert_physical.state, 'in_process', "Los certificados físicos deben transicionar a 'in_process'.")

    def test_08_idor_security_checks(self):
        """Test IDOR security checks: a student should not access other student's downloads/cancellations/success pages."""
        # 1. Crear solicitud para portal_user
        cert_req = self.env['irg.certificate.request'].sudo().create({
            'gradebook_student_id': self.gradebook_done.id,
            'document_type': 'gradebook',
            'certificate_type': 'digital',
            'signer': 'raimon',
            'state': 'pending_payment',
            'origin': 'portal',
        })

        # Autenticar como el otro estudiante
        self.authenticate(self.other_user.login, self.other_user.login)
        
        # Intentar descargar diploma ajeno
        diploma_url = f"/campus/certificates/download/diploma/{self.diploma.id}"
        response = self.url_open(diploma_url, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers.get('Location', '').endswith('/campus/certificates'))

        # Intentar descargar acta ajena
        acta_url = f"/campus/certificates/download/acta/{self.acta.id}"
        response = self.url_open(acta_url, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers.get('Location', '').endswith('/campus/certificates'))

        # Intentar acceder a success del pago ajeno
        success_url = f"/campus/certificates/payment/success/{cert_req.id}"
        response = self.url_open(success_url, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers.get('Location', '').endswith('/campus/certificates'))

        # Intentar acceder a cancel del pago ajeno
        cancel_url = f"/campus/certificates/payment/cancel/{cert_req.id}"
        response = self.url_open(cancel_url, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue('/campus/certificates' in response.headers.get('Location', ''))
        # Asegurarse de que el estado de la solicitud ajena no cambió a 'cancelled'
        cert_req.invalidate_model(['state'])
        self.assertEqual(cert_req.state, 'pending_payment', "El estado no debería haber cambiado a cancelado por otro usuario.")

        # Intentar acceder a thank-you ajeno
        thank_you_url = f"/campus/certificates/thank-you/{cert_req.id}"
        response = self.url_open(thank_you_url, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers.get('Location', '').endswith('/campus/certificates'))

        # Intentar pagar solicitud ajena
        pay_url = f"/campus/certificates/pay/{cert_req.id}"
        response = self.url_open(pay_url, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers.get('Location', '').endswith('/campus/certificates'))
