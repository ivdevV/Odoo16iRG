# -*- coding: utf-8 -*-
import base64

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from psycopg2 import IntegrityError
from odoo.tools import mute_logger


class TestOficialidadSummary(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Alumno Oficialidad',
            'email': 'oficialidad.alumno@example.com',
            'vat': '12345678Z',
        })
        self.type_titulo = self.env['irg.oficialidad.document.type'].search([
            ('key', '=', 'titulo-universitario'),
        ], limit=1)

    def _create_document(self, doc_type=None, **extra):
        values = {
            'partner_id': self.partner.id,
            'document_type_id': (doc_type or self.type_titulo).id,
            'name': 'Titulo universitario',
            'filename': 'titulo.pdf',
            'file': base64.b64encode(b'%PDF-1.4 test'),
        }
        values.update(extra)
        return self.env['irg.oficialidad.document'].create(values)

    def test_vat_hint_dni_nacional(self):
        hint = self.partner._irg_oficialidad_vat_hint_from_vat('12345678Z')
        self.assertEqual(hint, 'nacional')

    def test_vat_hint_nie_nacional(self):
        hint = self.partner._irg_oficialidad_vat_hint_from_vat('X1234567L')
        self.assertEqual(hint, 'nacional')

    def test_vat_hint_foreign_internacional(self):
        hint = self.partner._irg_oficialidad_vat_hint_from_vat('AB123456')
        self.assertEqual(hint, 'internacional')

    def test_vat_hint_es_prefix_and_separators(self):
        hint = self.partner._irg_oficialidad_vat_hint_from_vat(' es 12.345.678-z ')
        self.assertEqual(hint, 'nacional')

    def test_vat_hint_unknown_without_vat(self):
        self.assertEqual(self.partner._irg_oficialidad_vat_hint_from_vat(False), 'unknown')
        self.assertEqual(self.partner._irg_oficialidad_vat_hint_from_vat(''), 'unknown')

    def test_mismatch_when_app_says_internacional(self):
        self.partner.irg_oficialidad_student_type = 'internacional'
        self.assertTrue(self.partner.irg_oficialidad_type_mismatch)

    def test_no_mismatch_when_types_agree(self):
        self.partner.irg_oficialidad_student_type = 'nacional'
        self.assertEqual(self.partner.irg_oficialidad_vat_hint, 'nacional')
        self.assertFalse(self.partner.irg_oficialidad_type_mismatch)

    def test_no_mismatch_when_hint_unknown(self):
        self.partner.vat = False
        self.partner.irg_oficialidad_student_type = 'internacional'
        self.assertEqual(self.partner.irg_oficialidad_vat_hint, 'unknown')
        self.assertFalse(self.partner.irg_oficialidad_type_mismatch)

    def test_completeness_empty_without_student_type(self):
        self.assertEqual(self.partner.irg_oficialidad_expected_count, 0)
        self.assertEqual(self.partner.irg_oficialidad_received_count, 0)
        self.assertFalse(self.partner.irg_oficialidad_completeness)
        self.assertFalse(self.partner.irg_oficialidad_is_complete)

    def test_completeness_after_one_document(self):
        self.partner.irg_oficialidad_student_type = 'nacional'
        self._create_document()
        self.assertEqual(self.partner.irg_oficialidad_expected_count, 4)
        self.assertEqual(self.partner.irg_oficialidad_received_count, 1)
        self.assertEqual(self.partner.irg_oficialidad_completeness, '1/4')
        self.assertFalse(self.partner.irg_oficialidad_is_complete)
        self.assertTrue(self.partner.irg_oficialidad_last_received_at)

    def test_complete_when_all_expected_received(self):
        self.partner.irg_oficialidad_student_type = 'nacional'
        for key in self.env['irg.oficialidad.document.type'].get_expected_keys('nacional'):
            doc_type = self.env['irg.oficialidad.document.type'].search([('key', '=', key)], limit=1)
            self._create_document(doc_type=doc_type, name=key)
        self.assertEqual(self.partner.irg_oficialidad_completeness, '4/4')
        self.assertTrue(self.partner.irg_oficialidad_is_complete)

    def test_out_of_scope_document_not_counted(self):
        self.partner.irg_oficialidad_student_type = 'nacional'
        pasaporte = self.env['irg.oficialidad.document.type'].search([('key', '=', 'pasaporte')], limit=1)
        self._create_document(doc_type=pasaporte, name='Pasaporte')
        self.assertEqual(self.partner.irg_oficialidad_received_count, 0)
        self.assertEqual(self.partner.irg_oficialidad_completeness, '0/4')

    def test_checklist_html_lists_expected_types(self):
        self.partner.irg_oficialidad_student_type = 'nacional'
        self._create_document()
        html = str(self.partner.irg_oficialidad_checklist_html)
        self.assertIn('Título universitario', html)
        self.assertEqual(html.count('<li'), 4)

    def test_checklist_html_empty_without_student_type(self):
        self.assertFalse(self.partner.irg_oficialidad_checklist_html)

    def test_unique_partner_document_type(self):
        self._create_document()
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self._create_document()

    def test_attachment_not_public(self):
        doc = self._create_document()
        attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'irg.oficialidad.document'),
            ('res_id', '=', doc.id),
            ('res_field', '=', 'file'),
        ])
        self.assertTrue(attachments)
        self.assertFalse(any(attachments.mapped('public')))

    def test_state_default_and_actions(self):
        doc = self._create_document()
        self.assertEqual(doc.state, 'submitted')
        doc.action_accept()
        self.assertEqual(doc.state, 'accepted')
        doc.action_observe()
        self.assertEqual(doc.state, 'observed')
        doc.action_mark_submitted()
        self.assertEqual(doc.state, 'submitted')

    def test_name_get_includes_partner(self):
        doc = self._create_document()
        self.assertIn('Alumno Oficialidad', doc.display_name)

    def test_student_related_fields(self):
        self.partner.irg_oficialidad_student_type = 'nacional'
        self._create_document()
        student = self.env['op.student'].create({
            'partner_id': self.partner.id,
            'first_name': 'Alumno',
            'last_name': 'Oficialidad',
            'birth_date': '2000-01-01',
            'gender': 'm',
        })
        self.assertEqual(student.irg_oficialidad_student_type, 'nacional')
        self.assertEqual(student.irg_oficialidad_completeness, '1/4')
        self.assertEqual(len(student.irg_oficialidad_document_ids), 1)

    def test_no_acl_for_portal_or_public(self):
        acls = self.env['ir.model.access'].sudo().search([
            ('model_id.model', '=', 'irg.oficialidad.document'),
        ])
        self.assertTrue(acls)
        portal = self.env.ref('base.group_portal')
        public = self.env.ref('base.group_public')
        self.assertFalse(acls.filtered(lambda a: a.group_id in (portal | public)))
        self.assertFalse(acls.filtered(lambda a: not a.group_id))

    def test_portal_user_cannot_read_documents(self):
        doc = self._create_document()
        portal_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Portal Oficialidad',
            'login': 'portal.oficialidad@example.com',
            'email': 'portal.oficialidad@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        with self.assertRaises(AccessError):
            doc.with_user(portal_user).read(['name'])
