# -*- coding: utf-8 -*-
import base64

from lxml import etree

from odoo.tests.common import TransactionCase


class TestPracticeCenterDocumentsConsistency(TransactionCase):

    def test_practice_center_has_readonly_display_field(self):
        field = self.env['practice.center']._fields.get('document_display_ids')

        self.assertIsNotNone(field)
        self.assertEqual(field.type, 'many2many')
        self.assertEqual(field.comodel_name, 'ir.attachment')
        self.assertTrue(field.readonly)

    def test_documents_section_uses_distinct_readonly_field(self):
        view = self.env.ref('isep_practices_2.view_practice_center_form')
        arch = view.get_combined_arch()
        root = etree.fromstring(arch.encode())

        editable_fields = root.xpath(
            "//field[@name='document_ids' and @widget='many2many_binary']"
        )
        duplicate_document_fields = root.xpath(
            "//field[@name='document_ids' and not(@widget)]"
        )
        display_fields = root.xpath("//field[@name='document_display_ids']")
        display_name_fields = root.xpath(
            "//field[@name='document_display_ids']/tree/field[@name='name']"
        )

        self.assertEqual(len(editable_fields), 1)
        self.assertFalse(duplicate_document_fields)
        self.assertEqual(len(display_fields), 1)
        self.assertTrue(display_name_fields)
        self.assertEqual(display_name_fields[0].get('string'), 'Document Name')

    def test_document_attachment_persists_and_is_normalized(self):
        center = self.env['practice.center'].create({
            'name': 'Test Practice Center',
            'email': 'center@example.com',
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'agreement.pdf',
            'datas': base64.b64encode(b'agreement').decode('ascii'),
            'type': 'binary',
        })

        center.write({'document_ids': [(6, 0, [attachment.id])]})
        center.invalidate_recordset(['document_ids', 'document_display_ids'])
        attachment.invalidate_recordset(['res_model', 'res_id'])

        self.assertEqual(center.document_ids, attachment)
        self.assertEqual(center.document_display_ids, attachment)
        self.assertEqual(attachment.res_model, 'practice.center')
        self.assertEqual(attachment.res_id, center.id)

    def test_existing_linked_attachment_is_not_reassigned(self):
        partner = self.env['res.partner'].create({'name': 'Attachment Owner'})
        center = self.env['practice.center'].create({
            'name': 'Test Practice Center',
            'email': 'center@example.com',
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'partner-document.pdf',
            'datas': base64.b64encode(b'partner-document').decode('ascii'),
            'type': 'binary',
            'res_model': 'res.partner',
            'res_id': partner.id,
        })

        center.write({'document_ids': [(6, 0, [attachment.id])]})
        attachment.invalidate_recordset(['res_model', 'res_id'])

        self.assertEqual(center.document_ids, attachment)
        self.assertEqual(attachment.res_model, 'res.partner')
        self.assertEqual(attachment.res_id, partner.id)
