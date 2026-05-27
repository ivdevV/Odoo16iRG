# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase


class TestPracticeCenterDocuments(TransactionCase):

    def test_practice_center_has_document_attachment_field(self):
        field = self.env['practice.center']._fields.get('document_ids')

        self.assertIsNotNone(field)
        self.assertEqual(field.type, 'many2many')
        self.assertEqual(field.comodel_name, 'ir.attachment')

    def test_documents_section_is_before_practice_schedules(self):
        view = self.env.ref('isep_practices_2.view_practice_center_form')
        arch = view.read_combined(['arch'])['arch']
        root = etree.fromstring(arch.encode())

        document_fields = root.xpath("//field[@name='document_ids']")
        schedule_groups = root.xpath("//group[@string='Practice Schedules']")

        self.assertTrue(document_fields)
        self.assertTrue(schedule_groups)
        self.assertLess(
            arch.index('name="document_ids"'),
            arch.index('string="Practice Schedules"'),
        )

    def test_documents_section_shows_attachment_names(self):
        view = self.env.ref('isep_practices_2.view_practice_center_form')
        arch = view.read_combined(['arch'])['arch']
        root = etree.fromstring(arch.encode())

        document_name_fields = root.xpath(
            "//field[@name='document_ids']/tree/field[@name='name']"
        )

        self.assertTrue(document_name_fields)
        self.assertEqual(document_name_fields[0].get('string'), 'Document Name')
