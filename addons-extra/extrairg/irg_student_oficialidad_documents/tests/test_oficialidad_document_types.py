# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestOficialidadDocumentTypes(TransactionCase):
    def test_catalogue_has_seven_keys(self):
        Type = self.env['irg.oficialidad.document.type']
        keys = set(Type.search([]).mapped('key'))
        self.assertEqual(keys, {
            'titulo-universitario',
            'certificado-notas',
            'documento-identificativo-nacional',
            'titulo-universitario-apostillado',
            'apostilla-certificado-notas',
            'pasaporte',
            'matricula-unimarconi',
        })

    def test_expected_keys_nacional(self):
        Type = self.env['irg.oficialidad.document.type']
        self.assertEqual(
            Type.get_expected_keys('nacional'),
            [
                'titulo-universitario',
                'certificado-notas',
                'matricula-unimarconi',
                'documento-identificativo-nacional',
            ],
        )

    def test_expected_keys_internacional(self):
        Type = self.env['irg.oficialidad.document.type']
        self.assertEqual(
            Type.get_expected_keys('internacional'),
            [
                'titulo-universitario-apostillado',
                'apostilla-certificado-notas',
                'matricula-unimarconi',
                'pasaporte',
            ],
        )

    def test_matricula_scope_both(self):
        matricula = self.env['irg.oficialidad.document.type'].search([
            ('key', '=', 'matricula-unimarconi'),
        ], limit=1)
        self.assertEqual(matricula.student_type_scope, 'both')
