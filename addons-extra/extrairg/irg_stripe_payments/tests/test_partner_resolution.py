# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import tagged

from .common import StripePaymentsCommon


@tagged('post_install', '-at_install')
class TestPartnerResolution(StripePaymentsCommon):

    def test_01_match_by_stored_customer_id(self):
        partner = self._make_partner('Ana', 'ana@test.com', irg_stripe_customer_id='cus_A')
        result = self.sync._resolve_partner('cus_A')
        self.assertEqual(result['partner'], partner)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['method'], 'stripe_customer_id')

    def test_02_match_by_customer_metadata(self):
        partner = self._make_partner('Bea', 'bea@test.com')
        payload = {'id': 'cus_B', 'email': 'bea@test.com',
                   'metadata': {'odoo_partner_id': str(partner.id)}}
        with patch.object(type(self.provider), '_stripe_make_request', return_value=payload):
            result = self.sync._resolve_partner('cus_B')
        self.assertEqual(result['partner'], partner)
        self.assertEqual(result['method'], 'customer_metadata')
        # El customer id queda guardado para que el próximo pago no necesite la API.
        self.assertEqual(partner.irg_stripe_customer_id, 'cus_B')

    def test_03_ambiguous_email_does_not_guess(self):
        """El caso que motiva todo el endurecimiento.

        Dos contactos activos con el mismo email: antes se cogía el primero y se le
        escribía encima el customer id. Ahora no se elige ninguno.
        """
        first = self._make_partner('Carlos Uno', 'dup@test.com')
        second = self._make_partner('Carlos Dos', 'dup@test.com')

        result = self.sync._resolve_partner(False, email='dup@test.com')

        self.assertFalse(result['partner'])
        self.assertEqual(result['status'], 'ambiguous_email')
        self.assertEqual(set(result['candidates'].ids), {first.id, second.id})

        reviews = self.review_obj.search([
            ('reason', '=', 'ambiguous_email'), ('stripe_email', '=', 'dup@test.com')])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(len(reviews.candidate_partner_ids), 2)

        # Y, crucialmente, no se ha escrito nada en ninguno de los dos.
        self.assertFalse(first.irg_stripe_customer_id)
        self.assertFalse(second.irg_stripe_customer_id)

    def test_04_archived_partner_is_excluded(self):
        active = self._make_partner('Dora Activa', 'dora@test.com')
        archived = self._make_partner('Dora Vieja', 'dora@test.com')
        archived.active = False

        result = self.sync._resolve_partner(False, email='dora@test.com')

        self.assertEqual(result['partner'], active)
        self.assertEqual(result['status'], 'matched')

    def test_05_student_wins_over_plain_contact(self):
        student_partner = self._make_partner('Eva Alumna', 'eva@test.com')
        self._make_student(student_partner)
        self._make_partner('Eva Contacto', 'eva@test.com')

        result = self.sync._resolve_partner(False, email='eva@test.com')

        self.assertEqual(result['partner'], student_partner)
        self.assertEqual(result['method'], 'student_email_unique')

    def test_06_email_is_case_and_space_insensitive(self):
        partner = self._make_partner('Fran', 'fran@test.com')
        result = self.sync._resolve_partner(False, email='  FRAN@Test.COM ')
        self.assertEqual(result['partner'], partner)

    def test_07_conflicting_customer_id_is_not_overwritten(self):
        """Segundo bug: el write era incondicional y pisaba un customer id distinto."""
        partner = self._make_partner('Gema', 'gema@test.com', irg_stripe_customer_id='cus_OLD')

        linked = self.sync._irg_link_customer_id(partner, 'cus_NEW')

        self.assertFalse(linked)
        self.assertEqual(partner.irg_stripe_customer_id, 'cus_OLD')
        self.assertTrue(self.review_obj.search([
            ('reason', '=', 'conflicting_customer_id'),
            ('stripe_customer_id', '=', 'cus_NEW')]))

    def test_08_two_partners_share_customer_id(self):
        self._make_partner('Hugo A', 'hugoa@test.com', irg_stripe_customer_id='cus_DUP')
        self._make_partner('Hugo B', 'hugob@test.com', irg_stripe_customer_id='cus_DUP')

        result = self.sync._resolve_partner('cus_DUP')

        self.assertFalse(result['partner'])
        self.assertEqual(result['status'], 'conflicting_customer_id')

    def test_09_legacy_wrapper_returns_recordset(self):
        """`_find_partner` conserva su contrato: siempre devuelve un recordset."""
        self._make_partner('Iris Uno', 'iris@test.com')
        self._make_partner('Iris Dos', 'iris@test.com')

        partner = self.sync._find_partner(False, email='iris@test.com')

        self.assertEqual(partner._name, 'res.partner')
        self.assertFalse(partner)

    def test_10_email_mode_disabled_skips_email_tier(self):
        self._make_partner('Julia', 'julia@test.com')
        self._set_email_mode('disabled')

        result = self.sync._resolve_partner(False, email='julia@test.com')

        self.assertFalse(result['partner'])
        self.assertEqual(result['status'], 'not_found')

    def test_11_email_mode_legacy_restores_old_behaviour(self):
        """Vía de escape sin redespliegue: vuelve a elegir el primero."""
        self._make_partner('Kira Uno', 'kira@test.com')
        self._make_partner('Kira Dos', 'kira@test.com')
        self._set_email_mode('legacy')

        result = self.sync._resolve_partner(False, email='kira@test.com')

        self.assertTrue(result['partner'])
        self.assertEqual(result['method'], 'email_unique')

    def test_12_repeated_ambiguity_bumps_occurrence(self):
        self._make_partner('Luis Uno', 'luis@test.com')
        self._make_partner('Luis Dos', 'luis@test.com')

        self.sync._resolve_partner(False, email='luis@test.com')
        self.sync._resolve_partner(False, email='luis@test.com')

        reviews = self.review_obj.search([
            ('reason', '=', 'ambiguous_email'), ('stripe_email', '=', 'luis@test.com')])
        self.assertEqual(len(reviews), 1, "No debe crear una revisión por evento")
        self.assertEqual(reviews.occurrence_count, 2)

    def test_13_company_is_deprioritised_over_person(self):
        company = self._make_partner('Marta SL', 'marta@test.com', is_company=True)
        person = self._make_partner('Marta Pérez', 'marta@test.com')

        result = self.sync._resolve_partner(False, email='marta@test.com')

        self.assertEqual(result['partner'], person)
        self.assertNotEqual(result['partner'], company)

    def test_14_child_address_is_deprioritised(self):
        parent = self._make_partner('Nora', 'nora@test.com')
        self.env['res.partner'].sudo().create({
            'name': 'Nora Facturación',
            'email': 'nora@test.com',
            'type': 'invoice',
            'parent_id': parent.id,
        })

        result = self.sync._resolve_partner(False, email='nora@test.com')

        self.assertEqual(result['partner'], parent)

    def test_15_metadata_pointing_to_missing_partner_is_queued(self):
        payload = {'id': 'cus_GHOST', 'email': False,
                   'metadata': {'odoo_partner_id': '999999999'}}
        with patch.object(type(self.provider), '_stripe_make_request', return_value=payload):
            result = self.sync._resolve_partner('cus_GHOST')

        self.assertFalse(result['partner'])
        self.assertEqual(result['status'], 'metadata_partner_missing')
        self.assertTrue(self.review_obj.search([
            ('reason', '=', 'metadata_partner_missing'),
            ('stripe_customer_id', '=', 'cus_GHOST')]))
