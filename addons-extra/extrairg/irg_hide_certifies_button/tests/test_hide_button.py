# -*- coding: utf-8 -*-
"""
Tests para irg_hide_certifies_button.

El formulario de op.student no debe mostrar el botón legacy
"Certifies / Diplomas" (isep_openeducat_reports).
"""
from odoo.tests.common import TransactionCase


class TestHideCertifiesButton(TransactionCase):

    def _get_student_form_arch(self):
        view = self.env.ref('openeducat_core.view_op_student_form')
        return self.env['op.student'].get_view(
            view_id=view.id, view_type='form',
        )['arch']

    def test_certifies_button_hidden(self):
        """El botón "Certifies / Diplomas" no debe estar en la vista combinada."""
        arch = self._get_student_form_arch()
        self.assertNotIn(
            'Certifies / Diplomas', arch,
            'El botón legacy "Certifies / Diplomas" debe estar oculto.',
        )
