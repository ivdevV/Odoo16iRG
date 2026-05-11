# -*- coding: utf-8 -*-

import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestScholarshipDocuments(TransactionCase):
    def setUp(self):
        super().setUp()
        self.scholarship_type = self.env['irg.scholarship.type'].create({
            'name': 'Beca de prueba',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Alumno Beca',
            'email': 'alumno.beca@example.com',
            'irg_scholarship_type_id': self.scholarship_type.id,
        })
        portal_group = self.env.ref('base.group_portal')
        self.portal_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Portal Alumno Beca',
            'login': 'portal.alumno.beca@example.com',
            'email': 'portal.alumno.beca@example.com',
            'partner_id': self.partner.id,
            'groups_id': [(6, 0, [portal_group.id])],
        })

    def test_partner_stores_scholarship_documents(self):
        document = self.env['irg.scholarship.document'].create({
            'partner_id': self.partner.id,
            'name': 'Documento de identidad',
            'filename': 'identidad.pdf',
            'file': base64.b64encode(b'test'),
        })

        self.assertEqual(document.scholarship_type_id, self.scholarship_type)
        self.assertIn(document, self.partner.irg_scholarship_document_ids)

    def test_portal_user_only_sees_own_documents(self):
        own_document = self.env['irg.scholarship.document'].create({
            'partner_id': self.partner.id,
            'name': 'Documento propio',
            'filename': 'propio.pdf',
            'file': base64.b64encode(b'own'),
        })
        other_partner = self.env['res.partner'].create({'name': 'Otro Alumno'})
        self.env['irg.scholarship.document'].create({
            'partner_id': other_partner.id,
            'name': 'Documento ajeno',
            'filename': 'ajeno.pdf',
            'file': base64.b64encode(b'other'),
        })

        portal_documents = self.env['irg.scholarship.document'].with_user(self.portal_user).search([])
        self.assertEqual(portal_documents, own_document)
