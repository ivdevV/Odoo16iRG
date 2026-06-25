# -*- coding: utf-8 -*-
import base64
import re

from odoo.addons.mail.tests.common import mail_new_test_user
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install', 'irg_diplomado_portal_request')
class TestDiplomadoPortalRequest(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._original_compute_final_subject_note = type(cls.env['app.gradebook.subject']).compute_final_subject_note

        def _mock_compute_final_subject_note(self):
            for rec in self:
                if rec.op_subject_id.code == 'DIPOKPORTAL':
                    rec.final_subject_note = 8.5
                elif rec.op_subject_id.code == 'DIPLOWPORTAL':
                    rec.final_subject_note = 7.0
                else:
                    rec.final_subject_note = 0.0

        type(cls.env['app.gradebook.subject']).compute_final_subject_note = _mock_compute_final_subject_note
        cls._original_action_reprint = type(cls.env['irg.diplomado.registry']).action_reprint

        def _mock_action_reprint(self):
            for record in self:
                attachment = record.env['ir.attachment'].sudo().create({
                    'name': 'diplomado_direct_download_test.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(b'DIPLOMADO_DIRECT_DOWNLOAD_PDF'),
                    'res_model': 'irg.diplomado.registry',
                    'res_id': record.id,
                    'mimetype': 'application/pdf',
                })
                record.attachment_id = attachment.id
            return True

        type(cls.env['irg.diplomado.registry']).action_reprint = _mock_action_reprint

        test_course_names = ('Diplomado Portal OK', 'Diplomado Portal LOW', 'Master Portal')
        cls.env['irg.diplomado.portal.request'].sudo().search([('course_id.name', 'in', test_course_names)]).unlink()
        cls.env['irg.diplomado.registry'].sudo().search([
            '|',
            ('name', 'in', ('DIP-PORTAL-OK', 'DIP-PORTAL-LOW')),
            ('course_id.name', 'in', test_course_names),
        ]).unlink()
        cls.env['app.gradebook.student'].sudo().search([('admission_id.name', 'in', ('ADM-DIP-OK-PORTAL', 'ADM-DIP-LOW-PORTAL', 'ADM-MASTER-PORTAL'))]).unlink()
        cls.env['op.subject'].sudo().search([('code', 'in', ('DIPOKPORTAL', 'DIPLOWPORTAL'))]).unlink()
        cls.env['op.admission'].sudo().search([('name', 'in', ('ADM-DIP-OK-PORTAL', 'ADM-DIP-LOW-PORTAL', 'ADM-MASTER-PORTAL'))]).unlink()
        cls.env['op.admission.register'].sudo().search([('name', 'in', ('REG-DIP-OK-PORTAL', 'REG-DIP-LOW-PORTAL', 'REG-MASTER-PORTAL'))]).unlink()
        cls.env['op.batch'].sudo().search([('name', 'in', ('Batch DIP OK Portal', 'Batch DIP LOW Portal', 'Batch Master Portal'))]).unlink()
        cls.env['op.course'].sudo().search([('name', 'in', ('Diplomado Portal OK', 'Diplomado Portal LOW', 'Master Portal'))]).unlink()
        cls.env['res.users'].sudo().search([('login', '=', 'student_dip_portal_request')]).unlink()

        cls.portal_user = mail_new_test_user(
            cls.env,
            name='student_dip_portal_request',
            login='student_dip_portal_request',
            email='student_dip_portal_request@example.com',
            groups='base.group_portal',
        )
        cls.student = cls.env['op.student'].sudo().create({
            'partner_id': cls.portal_user.partner_id.id,
            'first_name': 'DiplomadoPortal',
            'last_name': 'Alumno',
        })

        cls.course_ok = cls.env['op.course'].sudo().create({'name': 'Diplomado Portal OK', 'code': 'DIPPORTALOK'})
        cls.course_low = cls.env['op.course'].sudo().create({'name': 'Diplomado Portal LOW', 'code': 'DIPPORTALLOW'})
        cls.course_master = cls.env['op.course'].sudo().create({'name': 'Master Portal', 'code': 'MSTPORTAL'})

        cls.batch_ok = cls.env['op.batch'].sudo().create({
            'name': 'Batch DIP OK Portal',
            'code': 'BDIPOK',
            'course_id': cls.course_ok.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        cls.batch_low = cls.env['op.batch'].sudo().create({
            'name': 'Batch DIP LOW Portal',
            'code': 'BDIPLOW',
            'course_id': cls.course_low.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        cls.batch_master = cls.env['op.batch'].sudo().create({
            'name': 'Batch Master Portal',
            'code': 'BMASTER',
            'course_id': cls.course_master.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        cls.product = cls.env['product.product'].sudo().create({'name': 'Product DIP Portal Request', 'type': 'service'})

        cls.register_ok = cls.env['op.admission.register'].sudo().create({
            'name': 'REG-DIP-OK-PORTAL',
            'course_id': cls.course_ok.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.register_low = cls.env['op.admission.register'].sudo().create({
            'name': 'REG-DIP-LOW-PORTAL',
            'course_id': cls.course_low.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.register_master = cls.env['op.admission.register'].sudo().create({
            'name': 'REG-MASTER-PORTAL',
            'course_id': cls.course_master.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })

        cls.admission_ok = cls._create_admission('ADM-DIP-OK-PORTAL', cls.course_ok, cls.batch_ok, cls.register_ok)
        cls.admission_low = cls._create_admission('ADM-DIP-LOW-PORTAL', cls.course_low, cls.batch_low, cls.register_low)
        cls.admission_master = cls._create_admission('ADM-MASTER-PORTAL', cls.course_master, cls.batch_master, cls.register_master)

        cls.gradebook_ok = cls._create_gradebook(cls.admission_ok, 'DIPOKPORTAL', 8.5)
        cls.gradebook_low = cls._create_gradebook(cls.admission_low, 'DIPLOWPORTAL', 7.0)
        cls.gradebook_master = cls.env['app.gradebook.student'].sudo().create({
            'admission_id': cls.admission_master.id,
            'state': 'done',
        })

        cls.attachment = cls.env['ir.attachment'].sudo().create({
            'name': 'diplomado_portal_test.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'DIPLOMADO_PORTAL_PDF'),
            'mimetype': 'application/pdf',
        })
        cls.env.cr.commit()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, '_original_compute_final_subject_note'):
            type(cls.env['app.gradebook.subject']).compute_final_subject_note = cls._original_compute_final_subject_note
        if hasattr(cls, '_original_action_reprint'):
            type(cls.env['irg.diplomado.registry']).action_reprint = cls._original_action_reprint
        super().tearDownClass()

    @classmethod
    def _create_admission(cls, name, course, batch, register):
        return cls.env['op.admission'].sudo().create({
            'name': name,
            'partner_id': cls.portal_user.partner_id.id,
            'student_id': cls.student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'register_id': register.id,
            'gender': 'm',
            'first_name': 'DiplomadoPortal',
            'last_name': 'Alumno',
        })

    @classmethod
    def _create_gradebook(cls, admission, subject_code, note):
        gradebook = cls.env['app.gradebook.student'].sudo().create({
            'admission_id': admission.id,
            'state': 'done',
        })
        subject = cls.env['op.subject'].sudo().create({
            'name': subject_code,
            'code': subject_code,
            'course_id': admission.course_id.id,
            'subject_type': 'compulsory',
        })
        gradebook_subject = cls.env['app.gradebook.subject'].sudo().create({
            'gradebook_student_id': gradebook.id,
            'op_subject_id': subject.id,
        })
        gradebook_subject.compute_final_subject_note()
        gradebook._amount_prod_final()
        return gradebook

    def _get_csrf(self, html):
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
        return match.group(1) if match else None

    def test_portal_page_and_request_requires_grade_above_seven(self):
        self.authenticate('student_dip_portal_request', 'student_dip_portal_request')

        response_ok = self.url_open('/campus/diplomados/%s' % self.course_ok.id)
        self.assertEqual(response_ok.status_code, 200)
        self.assertIn('Descargar Diploma', response_ok.text)
        self.assertIn('8.50', response_ok.text)

        csrf = self._get_csrf(response_ok.text)
        post_data = {}
        if csrf:
            post_data['csrf_token'] = csrf
        response_post = self.url_open('/campus/diplomados/%s/request' % self.course_ok.id, data=post_data)
        self.assertEqual(response_post.status_code, 200)
        self.assertEqual(response_post.content, b'DIPLOMADO_DIRECT_DOWNLOAD_PDF')

        request_record = self.env['irg.diplomado.portal.request'].sudo().search([
            ('student_id', '=', self.student.id),
            ('course_id', '=', self.course_ok.id),
        ], limit=1)
        self.assertFalse(request_record)
        registry = self.env['irg.diplomado.registry'].sudo().search([
            ('student_id', '=', self.student.id),
            ('course_id', '=', self.course_ok.id),
        ], limit=1)
        self.assertTrue(registry)
        self.assertTrue(registry.attachment_id)

        response_low = self.url_open('/campus/diplomados/%s' % self.course_low.id)
        self.assertEqual(response_low.status_code, 200)
        self.assertIn('7.00', response_low.text)
        self.assertNotIn('Descargar Diploma', response_low.text)

    def test_registry_links_request_and_download_is_secure(self):
        self.authenticate('student_dip_portal_request', 'student_dip_portal_request')
        request_record = self.env['irg.diplomado.portal.request'].sudo().create({
            'student_id': self.student.id,
            'course_id': self.course_ok.id,
            'gradebook_student_id': self.gradebook_ok.id,
            'final_grade': self.gradebook_ok.total_final,
            'state': 'requested',
        })

        registry = self.env['irg.diplomado.registry'].sudo().create({
            'name': 'DIP-PORTAL-OK',
            'student_id': self.student.id,
            'student_name': 'DiplomadoPortal Alumno',
            'course_id': self.course_ok.id,
            'diplomado_name': self.course_ok.name,
            'issue_date': '2026-06-16',
            'diploma_type': 'digital',
            'attachment_id': self.attachment.id,
        })
        self.assertEqual(request_record.state, 'processed')
        self.assertEqual(request_record.diplomado_registry_id, registry)

        response = self.url_open('/campus/diplomados/download/%s' % registry.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'DIPLOMADO_PORTAL_PDF')

    def test_course_tile_is_specific_for_diplomado(self):
        view = self.env.ref('irg_diplomado_portal_request.course_diplomado_specific_tile')
        arch = view.arch_db
        self.assertIn('Diploma Campus Internacional', arch)
        self.assertIn('/campus/diplomados/#{op_course_id}', arch)
        self.assertIn('course_id.irg_is_diplomado()', arch)
