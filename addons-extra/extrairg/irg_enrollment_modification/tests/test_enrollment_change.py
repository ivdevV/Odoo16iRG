# -*- coding: utf-8 -*-

import base64
import io
import zipfile
from xml.etree import ElementTree as ET

from lxml import etree
from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged


def _docx_text(attachment):
    data = base64.b64decode(attachment.datas)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        xml = archive.read('word/document.xml')
    root = ET.fromstring(xml)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    return ''.join(node.text or '' for node in root.findall('.//w:t', ns))


@tagged('post_install', '-at_install', 'irg_enrollment_modification')
class TestEnrollmentChange(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.academic = new_test_user(
            cls.env,
            login='enroll.acad@example.test',
            groups='irg_enrollment_modification.group_academic',
            name='Academic Enroll',
        )
        cls.accountant = new_test_user(
            cls.env,
            login='enroll.acct@example.test',
            groups='account.group_account_invoice',
            name='Accounting Enroll',
        )
        cls.product = cls.env['product.product'].create({
            'name': 'Enrollment Change Service',
            'type': 'service',
            'list_price': 10.0,
        })
        cls.year_origin = cls.env['op.academic.year'].create({
            'name': 'Año origen ENR',
            'start_date': '2025-09-01',
            'end_date': '2026-07-31',
        })
        cls.year_dest = cls.env['op.academic.year'].create({
            'name': 'Año destino ENR',
            'start_date': '2026-09-01',
            'end_date': '2027-07-31',
        })
        cls.course = cls._create_course('Curso origen ENR', 'ENR-C1')
        cls.course_dest = cls._create_course('Curso destino ENR', 'ENR-C2')
        cls.batch = cls._create_batch('Lote origen ENR', 'ENR-B1', cls.course)
        cls.batch_dest = cls._create_batch('Lote dest ENR', 'ENR-B2', cls.course)
        cls.batch_other_course = cls._create_batch(
            'Lote otro curso', 'ENR-B3', cls.course_dest,
        )
        cls.pay_origin = cls.env['account.payment.mode'].create({
            'name': 'Pago origen ENR',
            'bank_account_link': 'variable',
            'payment_method_id': cls.env.ref(
                'account.account_payment_method_manual_in'
            ).id,
        })
        cls.pay_dest = cls.env['account.payment.mode'].create({
            'name': 'Pago destino ENR',
            'bank_account_link': 'variable',
            'payment_method_id': cls.env.ref(
                'account.account_payment_method_manual_in'
            ).id,
        })
        partner = cls.env['res.partner'].create({
            'name': 'Alumno Modificacion Matricula',
            'email': 'enroll.student@example.test',
        })
        cls.student = cls.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Alumno',
            'last_name': 'Modificacion Matricula',
            'gender': 'o',
        })
        cls.student_course = cls.env['op.student.course'].create({
            'student_id': cls.student.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'academic_years_id': cls.year_origin.id,
            'roll_number': 'ENR-ROLL-1',
        })
        cls.sale_order = cls._create_sale_order(partner, cls.course, cls.pay_origin)

    @classmethod
    def _create_course(cls, name, code):
        vals = {
            'name': name,
            'code': code,
            'evaluation_type': 'normal',
        }
        Course = cls.env['op.course']
        if 'lang' in Course._fields:
            vals['lang'] = cls.env.user.lang or 'en_US'
        if 'name_cat' in Course._fields:
            vals['name_cat'] = name
        course = Course.create(vals)
        if 'product_template_id' in Course._fields:
            course.product_template_id = cls.product.product_tmpl_id.id
        return course

    @classmethod
    def _create_batch(cls, name, code, course):
        return cls.env['op.batch'].create({
            'name': name,
            'code': code,
            'course_id': course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })

    @classmethod
    def _create_sale_order(cls, partner, course, payment_mode):
        vals = {
            'partner_id': partner.id,
            'payment_mode_id': payment_mode.id,
        }
        Order = cls.env['sale.order']
        if 'student_id' in Order._fields:
            vals['student_id'] = partner.id
        if 'course_id' in Order._fields:
            vals['course_id'] = course.id
        order = Order.create(vals)
        line_vals = {
            'order_id': order.id,
            'product_id': cls.product.id,
            'product_uom_qty': 1,
            'price_unit': 10.0,
        }
        Line = cls.env['sale.order.line']
        if 'x_studio_modalidad' in Line._fields:
            line_vals['x_studio_modalidad'] = 'Online'
        Line.create(line_vals)
        return order

    def _wizard(self, user=None, **vals):
        defaults = {
            'student_id': self.student.id,
            'student_course_id': self.student_course.id,
            'origin_course_id': self.course.id,
            'origin_batch_id': self.batch.id,
            'origin_year_id': self.year_origin.id,
            'sale_order_id': self.sale_order.id,
            'origin_payment_mode_id': self.pay_origin.id,
            'origin_modality': 'Online',
        }
        defaults.update(vals)
        env = self.env['irg.enrollment.change.wizard']
        if user:
            env = env.with_user(user)
        return env.create(defaults)

    def _create_batch_change(self, user=None):
        wizard = self._wizard(
            user or self.academic,
            change_batch=True,
            dest_batch_id=self.batch_dest.id,
        )
        action = wizard.action_create_request()
        return self.env['irg.enrollment.change'].browse(action['res_id'])

    def test_create_request_posts_word_without_writing_enrollment(self):
        origin_course = self.student_course.course_id
        origin_batch = self.student_course.batch_id
        origin_year = self.student_course.academic_years_id
        origin_pay = self.sale_order.payment_mode_id

        change = self._create_batch_change()

        self.assertEqual(change.state, 'submitted')
        self.assertTrue(change.request_attachment_id)
        self.assertEqual(change.request_attachment_id.name, 'solicitud.docx')
        self.assertEqual(self.student_course.course_id, origin_course)
        self.assertEqual(self.student_course.batch_id, origin_batch)
        self.assertEqual(self.student_course.academic_years_id, origin_year)
        self.assertEqual(self.sale_order.payment_mode_id, origin_pay)
        attachments = self.student.message_ids.mapped('attachment_ids')
        self.assertIn(change.request_attachment_id, attachments)

    def test_create_requires_at_least_one_change(self):
        wizard = self._wizard(self.academic)
        with self.assertRaises(ValidationError):
            wizard.action_create_request()

    def test_create_requires_destination(self):
        wizard = self._wizard(self.academic, change_batch=True)
        with self.assertRaises(ValidationError):
            wizard.action_create_request()

    def test_create_payment_requires_sale_order(self):
        wizard = self._wizard(
            self.academic,
            change_payment=True,
            sale_order_id=False,
            dest_payment_mode_id=self.pay_dest.id,
        )
        with self.assertRaises(ValidationError):
            wizard.action_create_request()

    def test_create_modality_requires_sale_order(self):
        wizard = self._wizard(
            self.academic,
            change_modality=True,
            dest_modality='Homeclass',
            sale_order_id=False,
        )
        with self.assertRaises(ValidationError):
            wizard.action_create_request()

    def test_academic_approve_writes_sale_line_modality(self):
        Line = self.env['sale.order.line']
        if 'x_studio_modalidad' not in Line._fields:
            self.skipTest('x_studio_modalidad is not installed on sale.order.line')
        wizard = self._wizard(
            self.academic,
            change_modality=True,
            dest_modality='Homeclass',
        )
        change = self.env['irg.enrollment.change'].browse(
            wizard.action_create_request()['res_id']
        )
        change.with_user(self.academic).action_approve_academic()
        self.assertEqual(change.state, 'done')
        self.assertTrue(all(
            line.x_studio_modalidad == 'Homeclass'
            for line in self.sale_order.order_line
        ))

    def test_dest_batch_must_match_course(self):
        wizard = self._wizard(
            self.academic,
            change_batch=True,
            dest_batch_id=self.batch_other_course.id,
        )
        with self.assertRaises(ValidationError):
            wizard.action_create_request()

    def test_docx_contains_student_and_destination_not_finance_mark(self):
        change = self._create_batch_change()
        text = _docx_text(change.request_attachment_id)
        self.assertIn(self.student.name, text)
        self.assertIn(self.batch_dest.name, text)
        self.assertNotIn('X ÁREA FINANCIERA', text)
        self.assertNotIn('X AREA FINANCIERA', text)

    def test_academic_approve_writes_marked_fields_and_closes_without_payment(self):
        change = self._create_batch_change()
        origin_pay = self.sale_order.payment_mode_id

        change.with_user(self.academic).action_approve_academic()

        self.assertEqual(self.student_course.batch_id, self.batch_dest)
        self.assertEqual(self.student_course.course_id, self.course)
        self.assertEqual(self.student_course.academic_years_id, self.year_origin)
        self.assertEqual(self.sale_order.payment_mode_id, origin_pay)
        self.assertEqual(change.state, 'done')
        if change.pdf_pending:
            self.assertFalse(change.final_attachment_id)
        else:
            self.assertTrue(change.final_attachment_id)
            self.assertEqual(change.final_attachment_id.mimetype, 'application/pdf')

    def test_academic_approve_waits_for_finance_when_payment_marked(self):
        wizard = self._wizard(
            self.academic,
            change_batch=True,
            dest_batch_id=self.batch_dest.id,
            change_payment=True,
            dest_payment_mode_id=self.pay_dest.id,
        )
        change = self.env['irg.enrollment.change'].browse(
            wizard.action_create_request()['res_id']
        )
        origin_pay = self.sale_order.payment_mode_id

        change.with_user(self.academic).action_approve_academic()

        self.assertEqual(change.state, 'academic_approved')
        self.assertEqual(self.student_course.batch_id, self.batch_dest)
        self.assertEqual(self.sale_order.payment_mode_id, origin_pay)
        self.assertFalse(change.final_attachment_id)

    def test_finance_approve_writes_payment_and_pdf(self):
        wizard = self._wizard(
            self.academic,
            change_year=True,
            dest_year_id=self.year_dest.id,
            change_payment=True,
            dest_payment_mode_id=self.pay_dest.id,
        )
        change = self.env['irg.enrollment.change'].browse(
            wizard.action_create_request()['res_id']
        )
        change.with_user(self.academic).action_approve_academic()
        change.with_user(self.accountant).action_approve_finance()

        self.assertEqual(self.sale_order.payment_mode_id, self.pay_dest)
        self.assertEqual(self.student_course.academic_years_id, self.year_dest)
        self.assertEqual(change.state, 'done')
        if not change.pdf_pending:
            text = _docx_text(change.request_attachment_id)
            self.assertIn(self.student.name, text)
            self.assertTrue(change.final_attachment_id)

    def test_accountant_cannot_approve_academic(self):
        change = self._create_batch_change()
        origin_batch = self.student_course.batch_id
        with self.assertRaises(AccessError):
            change.with_user(self.accountant).action_approve_academic()
        self.assertEqual(self.student_course.batch_id, origin_batch)
        self.assertEqual(change.state, 'submitted')

    def test_academic_cannot_approve_finance(self):
        wizard = self._wizard(
            self.academic,
            change_payment=True,
            dest_payment_mode_id=self.pay_dest.id,
        )
        change = self.env['irg.enrollment.change'].browse(
            wizard.action_create_request()['res_id']
        )
        change.with_user(self.academic).action_approve_academic()
        origin_pay = self.sale_order.payment_mode_id
        with self.assertRaises(AccessError):
            change.with_user(self.academic).action_approve_finance()
        self.assertEqual(self.sale_order.payment_mode_id, origin_pay)
        self.assertEqual(change.state, 'academic_approved')

    def test_accountant_cannot_create_request(self):
        with self.assertRaises(AccessError):
            self._wizard(
                self.accountant,
                change_batch=True,
                dest_batch_id=self.batch_dest.id,
            )

    def test_refuse_from_submitted_does_not_write(self):
        change = self._create_batch_change()
        origin_batch = self.student_course.batch_id
        origin_pay = self.sale_order.payment_mode_id

        change.with_user(self.academic).action_refuse()

        self.assertEqual(change.state, 'refused')
        self.assertEqual(self.student_course.batch_id, origin_batch)
        self.assertEqual(self.sale_order.payment_mode_id, origin_pay)
        self.assertFalse(change.final_attachment_id)

    def test_refuse_from_academic_approved_keeps_academic_does_not_write_payment(self):
        wizard = self._wizard(
            self.academic,
            change_batch=True,
            dest_batch_id=self.batch_dest.id,
            change_payment=True,
            dest_payment_mode_id=self.pay_dest.id,
        )
        change = self.env['irg.enrollment.change'].browse(
            wizard.action_create_request()['res_id']
        )
        change.with_user(self.academic).action_approve_academic()
        origin_pay = self.sale_order.payment_mode_id

        change.with_user(self.accountant).action_refuse()

        self.assertEqual(change.state, 'refused')
        self.assertEqual(self.student_course.batch_id, self.batch_dest)
        self.assertEqual(self.sale_order.payment_mode_id, origin_pay)
        self.assertFalse(change.final_attachment_id)

    def test_view_exposes_header_button(self):
        view = self.env.ref(
            'irg_enrollment_modification.view_op_student_form_enrollment_change'
        )
        arch = etree.fromstring(view.arch_db.encode())
        buttons = arch.xpath(
            "//button[@name='action_open_enrollment_change_wizard']"
        )
        self.assertEqual(len(buttons), 1)
        self.assertEqual(
            buttons[0].get('groups'),
            'irg_enrollment_modification.group_academic',
        )
        self.assertIn('oe_highlight', buttons[0].get('class', ''))

    def test_open_wizard_action_from_student(self):
        action = self.student.with_user(
            self.academic
        ).action_open_enrollment_change_wizard()
        self.assertEqual(action['res_model'], 'irg.enrollment.change.wizard')
        self.assertEqual(action['context']['default_student_id'], self.student.id)

    def test_faculty_student_cannot_open_wizard(self):
        with self.assertRaises(AccessError):
            self.student.with_user(
                self.accountant
            ).action_open_enrollment_change_wizard()
