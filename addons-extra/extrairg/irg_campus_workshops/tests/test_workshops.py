# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestCampusWorkshops(TransactionCase):

    def test_view_inheritance(self):
        """Verifica que la vista herede de forma correcta y contenga la sección Talleres y la tarjeta iRG Empower."""
        # Obtener la vista heredada por su external ID
        view = self.env.ref('irg_campus_workshops.irg_user_profile_content_workshops')
        self.assertTrue(view.active, "La vista heredada de talleres debe estar activa.")

        # Verificar que el arch de la vista heredada contiene la sección
        arch = view.arch
        self.assertIn('Talleres', arch, "La vista debe definir la sección Talleres.")
        self.assertIn('https://app.institutoraimongaja.com/slides/irg-empower-261', arch, "La tarjeta debe apuntar a la URL de redirección específica.")
        self.assertIn('irg_empower_logo.jpg', arch, "La tarjeta debe incluir la imagen del logo.")
