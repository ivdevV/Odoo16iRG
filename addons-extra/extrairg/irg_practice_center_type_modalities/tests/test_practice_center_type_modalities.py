# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestPracticeCenterTypeModalities(TransactionCase):

    def test_practice_center_type_selection_labels_are_updated(self):
        selection = dict(
            self.env['practice.center.type']._fields['type_of_practice'].selection
        )

        self.assertEqual(selection['on_site'], 'Presencial en España')
        self.assertEqual(selection['validation'], 'Convalidación por experiencia')
        self.assertEqual(selection['homeclass_sincronas'], 'HomeClass Sincronas')
        self.assertEqual(selection['homeclass_asincronas'], 'HomeClass Asincronas')

    def test_extra_practice_center_type_options_are_available_as_records(self):
        expected_xmlids = {
            'irg_practice_center_type_modalities.practice_center_type_on_site_origin':
                'Presencial País de Origen',
            'irg_practice_center_type_modalities.practice_center_type_tfm_validation':
                'Convalidación por TFM',
        }

        for xmlid, expected_label in expected_xmlids.items():
            record = self.env.ref(xmlid)
            self.assertTrue(record.is_available)
            self.assertEqual(record.name_get()[0][1], expected_label)
