# -*- coding: utf-8 -*-
import base64
from datetime import date

from odoo.addons.mail.tests.common import mail_new_test_user
from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_generacion_diplomados_class_start_date')
class TestDiplomadoClassStartDate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.course = self.env['op.course'].create({
            'name': 'Diplomado Fecha Clases',
            'code': 'DIPCLSDATE',
            'lang': self.env.user.lang or 'en_US',
        })
        self.batch = self.env['op.batch'].create({
            'name': 'Lote Fecha Clases',
            'code': 'LFC2026',
            'course_id': self.course.id,
            'start_date': '2026-01-10',
            'end_date': '2026-06-10',
            'date_start_class': '2026-03-15',
        })
        self.partner = self.env['res.partner'].create({'name': 'Alumno Fecha Clases'})
        self.student = self.env['op.student'].create({
            'first_name': 'Alumno',
            'last_name': 'Fecha Clases',
            'partner_id': self.partner.id,
        })
        self.student_course = self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'state': 'finished',
        })
        self.env.company.external_report_layout_id = self.env.ref(
            'web.external_layout_standard'
        ).id

    def _registry_vals(self, **overrides):
        vals = {
            'student_id': self.student.id,
            'student_name': 'Alumno Fecha Clases',
            'course_id': self.course.id,
            'diplomado_name': self.course.name,
            'start_date': '2026-01-10',
            'end_date': '2026-06-10',
            'diploma_type': 'digital',
        }
        vals.update(overrides)
        return vals

    def test_celebration_start_prefers_date_start_class(self):
        start = self.env['irg.diplomado.registry']._irg_celebration_start_from_batch(self.batch)
        self.assertEqual(start, date(2026, 3, 15))

    def test_celebration_start_falls_back_to_batch_start_date(self):
        self.env.cr.execute(
            'UPDATE op_batch SET date_start_class = NULL WHERE id = %s',
            [self.batch.id],
        )
        self.batch.invalidate_recordset(['date_start_class'])
        start = self.env['irg.diplomado.registry']._irg_celebration_start_from_batch(self.batch)
        self.assertEqual(start, date(2026, 1, 10))

    def test_wizard_onchange_uses_class_start_date(self):
        wizard = self.env['irg.diplomado.wizard'].create({
            'student_id': self.student.id,
        })
        wizard._onchange_student_id()
        self.assertEqual(wizard.start_date, date(2026, 3, 15))
        self.assertEqual(wizard.end_date, date(2026, 6, 10))

    def test_reprint_syncs_class_start_and_overwrites_same_attachment(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_old.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'OLD_DIPLOMADO_PDF'),
            'res_model': 'irg.diplomado.registry',
            'mimetype': 'application/pdf',
        })
        registry = self.env['irg.diplomado.registry'].create(
            self._registry_vals(attachment_id=attachment.id)
        )
        attachment.write({'res_id': registry.id})
        self.batch.write({'date_start_class': '2026-04-20'})
        action = registry.action_reprint()
        self.assertEqual(registry.start_date, date(2026, 4, 20))
        self.assertEqual(registry.end_date, date(2026, 6, 10))
        self.assertEqual(registry.attachment_id.id, attachment.id)
        self.assertEqual(
            registry._get_diplomado_pdf_data()['start_date'],
            '20/04/2026',
        )
        pdf = base64.b64decode(registry.attachment_id.datas)
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertNotEqual(pdf, b'OLD_DIPLOMADO_PDF')
        self.assertTrue(action['url'].startswith('/web/content/%s' % attachment.id))

    def test_reprint_without_batch_keeps_stored_start_date(self):
        self.student_course.unlink()
        attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_orphan.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'ORPHAN_PDF'),
            'res_model': 'irg.diplomado.registry',
            'mimetype': 'application/pdf',
        })
        registry = self.env['irg.diplomado.registry'].create(
            self._registry_vals(
                start_date='2025-12-01',
                attachment_id=attachment.id,
            )
        )
        attachment.write({'res_id': registry.id})
        registry.action_reprint()
        self.assertEqual(registry.start_date, date(2025, 12, 1))
        self.assertEqual(
            registry._get_diplomado_pdf_data()['start_date'],
            '01/12/2025',
        )
        pdf = base64.b64decode(registry.attachment_id.datas)
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertNotEqual(pdf, b'ORPHAN_PDF')
        self.assertEqual(registry.attachment_id.id, attachment.id)

    def test_reprint_render_failure_keeps_start_date_and_pdf(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_fail.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'OLD_DIPLOMADO_PDF'),
            'res_model': 'irg.diplomado.registry',
            'mimetype': 'application/pdf',
        })
        registry = self.env['irg.diplomado.registry'].create(
            self._registry_vals(attachment_id=attachment.id)
        )
        attachment.write({'res_id': registry.id})
        report_model = type(self.env['report.irg_generacion_diplomados.diplomado_pdf'])
        original = report_model.generate_diplomado_pdf

        def _boom(self, data):
            raise ValueError('boom')

        report_model.generate_diplomado_pdf = _boom
        try:
            with self.assertRaises(ValueError):
                registry.action_reprint()
        finally:
            report_model.generate_diplomado_pdf = original
        self.assertEqual(registry.start_date, date(2026, 1, 10))
        self.assertEqual(
            base64.b64decode(registry.attachment_id.datas),
            b'OLD_DIPLOMADO_PDF',
        )

    def test_download_refresh_only_when_stored_start_is_stale(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_skip.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'KEEP_ME'),
            'res_model': 'irg.diplomado.registry',
            'mimetype': 'application/pdf',
        })
        empty = self.env['irg.diplomado.registry'].create(
            self._registry_vals(start_date=False, attachment_id=attachment.id)
        )
        attachment.write({'res_id': empty.id})
        self.assertFalse(empty._irg_should_refresh_on_download())
        stale = self.env['irg.diplomado.registry'].create(self._registry_vals())
        stale_attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_stale.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'STALE'),
            'res_model': 'irg.diplomado.registry',
            'res_id': stale.id,
            'mimetype': 'application/pdf',
        })
        stale.attachment_id = stale_attachment
        self.assertTrue(stale._irg_should_refresh_on_download())


@tagged('post_install', '-at_install', 'irg_generacion_diplomados_class_start_date')
class TestDiplomadoClassStartDatePortal(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._original_compute_final_subject_note = type(
            cls.env['app.gradebook.subject']
        ).compute_final_subject_note

        def _mock_compute_final_subject_note(self):
            for rec in self:
                code = rec.op_subject_id.code
                if code == 'DIPCLSOKSUB':
                    rec.final_subject_note = 8.5
                elif code == 'DIPCLSLOWSUB':
                    rec.final_subject_note = 7.0
                else:
                    rec.final_subject_note = 0.0

        type(cls.env['app.gradebook.subject']).compute_final_subject_note = (
            _mock_compute_final_subject_note
        )

        names = ('Diplomado Class Start OK', 'Diplomado Class Start LOW')
        cls.env['irg.diplomado.registry'].sudo().search([
            ('course_id.name', 'in', names),
        ]).unlink()
        cls.env['app.gradebook.student'].sudo().search([
            ('admission_id.name', 'in', ('ADM-DIP-CLS-OK', 'ADM-DIP-CLS-LOW')),
        ]).unlink()
        cls.env['op.subject'].sudo().search([
            ('code', 'in', ('DIPCLSOKSUB', 'DIPCLSLOWSUB')),
        ]).unlink()
        cls.env['op.admission'].sudo().search([
            ('name', 'in', ('ADM-DIP-CLS-OK', 'ADM-DIP-CLS-LOW')),
        ]).unlink()
        cls.env['op.admission.register'].sudo().search([
            ('name', 'in', ('REG-DIP-CLS-OK', 'REG-DIP-CLS-LOW')),
        ]).unlink()
        cls.env['op.batch'].sudo().search([
            ('name', 'in', ('Batch DIP CLS OK', 'Batch DIP CLS LOW')),
        ]).unlink()
        cls.env['op.course'].sudo().search([('name', 'in', names)]).unlink()
        cls.env['res.users'].sudo().search([
            ('login', 'in', ('student_dip_class_start', 'student_dip_class_start_other')),
        ]).unlink()

        cls.portal_user = mail_new_test_user(
            cls.env,
            name='student_dip_class_start',
            login='student_dip_class_start',
            email='student_dip_class_start@example.com',
            groups='base.group_portal',
        )
        cls.other_user = mail_new_test_user(
            cls.env,
            name='student_dip_class_start_other',
            login='student_dip_class_start_other',
            email='student_dip_class_start_other@example.com',
            groups='base.group_portal',
        )
        cls.student = cls.env['op.student'].sudo().create({
            'partner_id': cls.portal_user.partner_id.id,
            'first_name': 'ClassStart',
            'last_name': 'Alumno',
        })
        lang = cls.env.user.lang or 'en_US'
        cls.course_ok = cls.env['op.course'].sudo().create({
            'name': 'Diplomado Class Start OK',
            'code': 'DIPCLSOK',
            'lang': lang,
        })
        cls.course_low = cls.env['op.course'].sudo().create({
            'name': 'Diplomado Class Start LOW',
            'code': 'DIPCLSLOW',
            'lang': lang,
        })
        cls.batch_ok = cls.env['op.batch'].sudo().create({
            'name': 'Batch DIP CLS OK',
            'code': 'BDIPCLSOK',
            'course_id': cls.course_ok.id,
            'start_date': '2026-01-10',
            'end_date': '2026-12-31',
            'date_start_class': '2026-03-15',
        })
        cls.batch_low = cls.env['op.batch'].sudo().create({
            'name': 'Batch DIP CLS LOW',
            'code': 'BDIPCLSLOW',
            'course_id': cls.course_low.id,
            'start_date': '2026-01-10',
            'end_date': '2026-12-31',
            'date_start_class': '2026-03-15',
        })
        cls.product = cls.env['product.product'].sudo().create({
            'name': 'Product DIP Class Start',
            'type': 'service',
        })
        cls.register_ok = cls.env['op.admission.register'].sudo().create({
            'name': 'REG-DIP-CLS-OK',
            'course_id': cls.course_ok.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.register_low = cls.env['op.admission.register'].sudo().create({
            'name': 'REG-DIP-CLS-LOW',
            'course_id': cls.course_low.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.admission_ok = cls._create_admission(
            'ADM-DIP-CLS-OK', cls.course_ok, cls.batch_ok, cls.register_ok
        )
        cls.admission_low = cls._create_admission(
            'ADM-DIP-CLS-LOW', cls.course_low, cls.batch_low, cls.register_low
        )
        cls.gradebook_ok = cls._create_gradebook(cls.admission_ok, 'DIPCLSOKSUB', 8.5)
        cls.gradebook_low = cls._create_gradebook(cls.admission_low, 'DIPCLSLOWSUB', 7.0)
        cls.env.cr.commit()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, '_original_compute_final_subject_note'):
            type(cls.env['app.gradebook.subject']).compute_final_subject_note = (
                cls._original_compute_final_subject_note
            )
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
            'first_name': 'ClassStart',
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

    def _create_registry(self, course, batch, start_date='2026-01-10'):
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'diplomado_class_start_old.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'OLD_PORTAL_DIPLOMADO_PDF'),
            'mimetype': 'application/pdf',
        })
        registry = self.env['irg.diplomado.registry'].sudo().create({
            'student_id': self.student.id,
            'student_name': 'ClassStart Alumno',
            'course_id': course.id,
            'diplomado_name': course.name,
            'start_date': start_date,
            'end_date': batch.end_date,
            'diploma_type': 'digital',
            'attachment_id': attachment.id,
        })
        attachment.write({
            'res_model': 'irg.diplomado.registry',
            'res_id': registry.id,
        })
        return registry, attachment

    def test_eligible_download_regenerates_class_start_date(self):
        registry, attachment = self._create_registry(self.course_ok, self.batch_ok)
        old_datas = attachment.datas
        self.authenticate('student_dip_class_start', 'student_dip_class_start')
        response = self.url_open('/campus/diplomados/download/%s' % registry.id)
        self.assertEqual(response.status_code, 200)
        registry.invalidate_recordset(['start_date', 'attachment_id'])
        attachment.invalidate_recordset(['datas'])
        self.assertEqual(registry.start_date, date(2026, 3, 15))
        self.assertEqual(
            registry._get_diplomado_pdf_data()['start_date'],
            '15/03/2026',
        )
        self.assertEqual(registry.attachment_id.id, attachment.id)
        self.assertNotEqual(attachment.datas, old_datas)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_foreign_partner_download_does_not_mutate(self):
        registry, attachment = self._create_registry(self.course_ok, self.batch_ok)
        old_start = registry.start_date
        old_datas = attachment.datas
        self.authenticate('student_dip_class_start_other', 'student_dip_class_start_other')
        response = self.url_open('/campus/diplomados/download/%s' % registry.id)
        self.assertIn(response.status_code, (200, 303, 302))
        registry.invalidate_recordset(['start_date'])
        attachment.invalidate_recordset(['datas'])
        self.assertEqual(registry.start_date, old_start)
        self.assertEqual(attachment.datas, old_datas)
        self.assertFalse(response.content.startswith(b'%PDF'))

    def test_low_grade_download_does_not_mutate(self):
        registry, attachment = self._create_registry(self.course_low, self.batch_low)
        old_start = registry.start_date
        old_datas = attachment.datas
        self.authenticate('student_dip_class_start', 'student_dip_class_start')
        response = self.url_open('/campus/diplomados/download/%s' % registry.id)
        self.assertIn(response.status_code, (200, 303, 302))
        registry.invalidate_recordset(['start_date'])
        attachment.invalidate_recordset(['datas'])
        self.assertEqual(registry.start_date, old_start)
        self.assertEqual(attachment.datas, old_datas)

    def test_campus_eligible_download_regenerates_class_start_date(self):
        registry, attachment = self._create_registry(self.course_ok, self.batch_ok)
        old_datas = attachment.datas
        self.authenticate('student_dip_class_start', 'student_dip_class_start')
        response = self.url_open(
            '/campus/certificates/download/diplomado/%s' % registry.id
        )
        self.assertEqual(response.status_code, 200)
        registry.invalidate_recordset(['start_date', 'attachment_id'])
        attachment.invalidate_recordset(['datas'])
        self.assertEqual(registry.start_date, date(2026, 3, 15))
        self.assertEqual(registry.attachment_id.id, attachment.id)
        self.assertNotEqual(attachment.datas, old_datas)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_campus_foreign_partner_download_does_not_mutate(self):
        registry, attachment = self._create_registry(self.course_ok, self.batch_ok)
        old_start = registry.start_date
        old_datas = attachment.datas
        self.authenticate('student_dip_class_start_other', 'student_dip_class_start_other')
        response = self.url_open(
            '/campus/certificates/download/diplomado/%s' % registry.id
        )
        self.assertIn(response.status_code, (200, 303, 302))
        registry.invalidate_recordset(['start_date'])
        attachment.invalidate_recordset(['datas'])
        self.assertEqual(registry.start_date, old_start)
        self.assertEqual(attachment.datas, old_datas)
        self.assertFalse(response.content.startswith(b'%PDF'))

    def test_campus_low_grade_download_does_not_mutate(self):
        registry, attachment = self._create_registry(self.course_low, self.batch_low)
        old_start = registry.start_date
        old_datas = attachment.datas
        self.authenticate('student_dip_class_start', 'student_dip_class_start')
        response = self.url_open(
            '/campus/certificates/download/diplomado/%s' % registry.id
        )
        self.assertIn(response.status_code, (200, 303, 302))
        registry.invalidate_recordset(['start_date'])
        attachment.invalidate_recordset(['datas'])
        self.assertEqual(registry.start_date, old_start)
        self.assertEqual(attachment.datas, old_datas)
