# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase


class TestPracticeCenterCif(TransactionCase):

    def test_practice_center_has_cif_field(self):
        field = self.env['practice.center']._fields.get('cif')

        self.assertIsNotNone(field)
        self.assertEqual(field.type, 'char')
        self.assertEqual(field.string, 'CIF')

    def test_cif_appears_on_form_tree_and_search(self):
        form = self.env.ref('isep_practices_2.view_practice_center_form')
        tree = self.env.ref('isep_practices_2.view_practice_center_tree')
        search = self.env.ref('isep_practices_2.view_practice_center_search')

        form_arch = form.read_combined(['arch'])['arch']
        tree_arch = tree.read_combined(['arch'])['arch']
        search_arch = search.read_combined(['arch'])['arch']
        form_root = etree.fromstring(form_arch.encode())

        official = form_root.xpath("//field[@name='official_name']")[0]
        self.assertEqual(official.getnext().get('name'), 'cif')
        self.assertIn('name="cif"', tree_arch)
        self.assertIn('name="cif"', search_arch)

    def test_generate_center_copies_cif_to_partner_vat(self):
        center = self.env['practice.center'].create({
            'name': 'Centro CIF',
            'cif': ' B12345678 ',
        })

        country = self.env.ref('base.es')
        center.country_id = country
        center.create_res_partner()

        self.assertTrue(center.partner_id)
        self.assertEqual(center.partner_id.vat, 'B12345678')
        self.assertEqual(center.partner_id.country_id, country)

    def test_generate_center_copies_cif_without_country(self):
        center = self.env['practice.center'].create({
            'name': 'Centro sin pais',
            'cif': 'B12345678',
            'country_id': False,
        })

        center.create_res_partner()

        self.assertEqual(center.partner_id.vat, 'B12345678')
        self.assertFalse(center.partner_id.country_id)

    def test_agreement_create_prefers_center_cif_over_partner_vat(self):
        partner = self.env['res.partner'].create({
            'name': 'Contacto con otro VAT',
            'vat': 'A00000000',
        })
        center = self.env['practice.center'].create({
            'name': 'Centro con CIF y contacto',
            'cif': 'B12345678',
            'partner_id': partner.id,
        })

        agreement = self.env['practice.agreement'].create({
            'practice_center_id': center.id,
        })

        self.assertEqual(agreement.center_vat, 'B12345678')

    def test_new_agreement_receives_center_cif_without_partner(self):
        center = self.env['practice.center'].create({
            'name': 'Centro sin partner',
            'cif': 'A87654321',
        })

        agreement = self.env['practice.agreement'].create({
            'practice_center_id': center.id,
        })

        self.assertEqual(agreement.center_vat, 'A87654321')

    def test_explicit_agreement_vat_is_kept(self):
        center = self.env['practice.center'].create({
            'name': 'Centro con CIF propio',
            'cif': 'A87654321',
        })

        agreement = self.env['practice.agreement'].create({
            'practice_center_id': center.id,
            'center_vat': 'B00000000',
        })

        self.assertEqual(agreement.center_vat, 'B00000000')

    def test_agreement_action_prefers_center_cif_over_partner_vat(self):
        partner = self.env['res.partner'].create({
            'name': 'Contacto antiguo',
            'vat': 'A00000000',
        })
        center = self.env['practice.center'].create({
            'name': 'Centro con ambos',
            'cif': 'B12345678',
            'partner_id': partner.id,
        })

        action = center.action_create_agreement()
        agreement = self.env['practice.agreement'].browse(action['res_id'])

        self.assertEqual(agreement.center_vat, 'B12345678')
