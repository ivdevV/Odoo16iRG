# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tests.common import TransactionCase


class TestMorosoBanner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.income_account = cls.env['account.account'].create({
            'name': 'Test Income IRG Moroso Banner',
            'code': 'TSTMORB',
            'account_type': 'income',
            'company_id': cls.env.company.id,
        })
        cls.receivable_account = cls.env['account.account'].create({
            'name': 'Test Receivable IRG Moroso Banner',
            'code': 'TSTRMOR',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'company_id': cls.env.company.id,
        })
        cls.sale_journal = cls.env['account.journal'].create({
            'name': 'Test Sales IRG Moroso Banner',
            'code': 'TSMOR',
            'type': 'sale',
            'company_id': cls.env.company.id,
            'default_account_id': cls.income_account.id,
        })
        cls.bank_account = cls.env['account.account'].create({
            'name': 'Test Bank IRG Moroso Banner',
            'code': 'TSTBMOR',
            'account_type': 'asset_cash',
            'company_id': cls.env.company.id,
        })
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Test Bank IRG Moroso Banner',
            'code': 'TBMOR',
            'type': 'bank',
            'company_id': cls.env.company.id,
            'default_account_id': cls.bank_account.id,
        })
        cls.bank_journal.inbound_payment_method_line_ids.write({
            'payment_account_id': cls.bank_account.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Course IRG Moroso Banner',
            'type': 'service',
            'list_price': 100.0,
            'property_account_income_id': cls.income_account.id,
        })

    def _partner(self, name):
        return self.env['res.partner'].create({
            'name': name,
            'property_account_receivable_id': self.receivable_account.id,
        })

    def _student(self, partner, first_name='Alumno'):
        return self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': first_name,
            'last_name': 'Moroso',
            'gender': 'm',
            'birth_date': '2000-01-01',
        })

    def _create_invoice(self, partner, move_type='out_invoice', post=True,
                        amount=100.0, student_partner=None):
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'journal_id': self.sale_journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'account_id': self.income_account.id,
                'quantity': 1.0,
                'price_unit': amount,
            })],
        })
        if student_partner:
            invoice.write({'irg_student_partner_id': student_partner.id})
        if post:
            invoice.action_post()
        return invoice

    def _notes(self, record, fragment):
        return record.message_ids.filtered(
            lambda message: fragment in (message.body or '')
        )

    def _pay(self, invoice, amount=None):
        vals = {
            'journal_id': self.bank_journal.id,
            'payment_date': fields.Date.today(),
        }
        if amount is not None:
            vals['amount'] = amount
        register = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create(vals)
        register.action_create_payments()
        invoice.invalidate_recordset()
        return invoice

    def test_zero_or_one_invoice_stays_current_without_note(self):
        partner = self._partner('Sin deuda')
        student = self._student(partner)

        self.assertFalse(partner.irg_is_moroso)
        self._create_invoice(partner)

        self.assertFalse(partner.irg_is_moroso)
        self.assertFalse(self._notes(partner, 'Pasa a moroso'))
        self.assertFalse(self._notes(student, 'Pasa a moroso'))

    def test_two_unpaid_invoices_mark_partner_and_student(self):
        partner = self._partner('Dos impagadas')
        student = self._student(partner)
        self._create_invoice(partner)
        self._create_invoice(partner)

        self.assertTrue(partner.irg_is_moroso)
        self.assertTrue(student.irg_is_moroso)
        self.assertTrue(self._notes(partner, 'Pasa a moroso. Facturas sin pagar: 2.'))
        self.assertTrue(self._notes(student, 'Pasa a moroso. Facturas sin pagar: 2.'))
        note = self._notes(partner, 'Pasa a moroso. Facturas sin pagar: 2.')
        self.assertEqual(note.subtype_id, self.env.ref('mail.mt_note'))

    def test_partial_invoice_counts_as_unpaid(self):
        partner = self._partner('Parcial')
        self._student(partner)
        first = self._create_invoice(partner)
        self._create_invoice(partner)
        self._pay(first, amount=40.0)

        self.assertEqual(first.payment_state, 'partial')
        self.assertTrue(partner.irg_is_moroso)
        self.assertTrue(self._notes(partner, 'Pasa a moroso. Facturas sin pagar: 2.'))

    def test_draft_refund_and_in_payment_do_not_count(self):
        partner = self._partner('Excluidas')
        self._student(partner)
        self._create_invoice(partner, post=False)
        self._create_invoice(partner, post=False)
        self._create_invoice(partner, move_type='out_refund')
        posted = self._create_invoice(partner)
        posted_two = self._create_invoice(partner)
        self.assertTrue(partner.irg_is_moroso)

        self.env.cr.execute(
            'UPDATE account_move SET payment_state = %s WHERE id IN %s',
            ['in_payment', (posted.id, posted_two.id)],
        )
        (posted | posted_two).invalidate_recordset(['payment_state'])
        partner._irg_recompute_moroso()

        self.assertFalse(partner.irg_is_moroso)
        self.assertTrue(self._notes(partner, 'Deja de ser moroso. Facturas sin pagar: 0.'))

    def test_third_party_invoice_counts_for_student_and_payer(self):
        payer = self._partner('Pagador')
        student_partner = self._partner('Hijo')
        student = self._student(student_partner)
        self._create_invoice(payer, student_partner=student_partner)
        self._create_invoice(payer, student_partner=student_partner)

        self.assertTrue(payer.irg_is_moroso)
        self.assertTrue(student_partner.irg_is_moroso)
        self.assertTrue(student.irg_is_moroso)
        self.assertFalse(self._notes(payer, 'alumno'))

    def test_two_children_mark_payer_only(self):
        payer = self._partner('Padre de dos')
        first_partner = self._partner('Hijo uno')
        second_partner = self._partner('Hijo dos')
        self._student(first_partner, first_name='Uno')
        self._student(second_partner, first_name='Dos')
        self._create_invoice(payer, student_partner=first_partner)
        self._create_invoice(payer, student_partner=second_partner)

        self.assertTrue(payer.irg_is_moroso)
        self.assertFalse(first_partner.irg_is_moroso)
        self.assertFalse(second_partner.irg_is_moroso)

    def test_paying_down_to_one_clears_flag_and_notes_once(self):
        partner = self._partner('Regulariza')
        student = self._student(partner)
        first = self._create_invoice(partner)
        self._create_invoice(partner)
        self.assertTrue(partner.irg_is_moroso)

        self._pay(first)

        self.assertEqual(first.payment_state, 'paid')
        self.assertFalse(partner.irg_is_moroso)
        self.assertEqual(
            len(self._notes(partner, 'Deja de ser moroso. Facturas sin pagar: 1.')),
            1,
        )
        self.assertEqual(
            len(self._notes(student, 'Deja de ser moroso. Facturas sin pagar: 1.')),
            1,
        )

    def test_unreconcile_restores_moroso_flag(self):
        partner = self._partner('Desconciliar')
        student = self._student(partner)
        first = self._create_invoice(partner)
        self._create_invoice(partner)
        self._pay(first)
        self.assertFalse(partner.irg_is_moroso)

        partials = (
            first.line_ids.matched_debit_ids | first.line_ids.matched_credit_ids
        )
        partials.unlink()

        self.assertTrue(partner.irg_is_moroso)
        self.assertEqual(
            len(self._notes(partner, 'Pasa a moroso. Facturas sin pagar: 2.')),
            2,
        )
        self.assertEqual(
            len(self._notes(student, 'Pasa a moroso. Facturas sin pagar: 2.')),
            2,
        )

    def test_repeated_recompute_and_cron_do_not_duplicate_notes(self):
        partner = self._partner('Idempotente')
        self._student(partner)
        self._create_invoice(partner)
        self._create_invoice(partner)
        before = len(partner.message_ids)

        partner._irg_recompute_moroso()
        self.env['res.partner']._cron_recompute_moroso()

        self.assertTrue(partner.irg_is_moroso)
        self.assertEqual(len(partner.message_ids), before)

    def test_partner_change_recomputes_both_sides(self):
        leaving = self._partner('Sale')
        entering = self._partner('Entra')
        self._student(leaving)
        self._student(entering)
        self._create_invoice(entering)
        staying = self._create_invoice(leaving)
        moving = self._create_invoice(leaving)
        self.assertTrue(leaving.irg_is_moroso)
        self.assertFalse(entering.irg_is_moroso)

        moving.write({'partner_id': entering.id})

        self.assertFalse(leaving.irg_is_moroso)
        self.assertTrue(entering.irg_is_moroso)
        self.assertEqual(staying.partner_id, leaving)
        self.assertTrue(self._notes(leaving, 'Deja de ser moroso. Facturas sin pagar: 1.'))
        self.assertTrue(self._notes(entering, 'Pasa a moroso. Facturas sin pagar: 2.'))

    def test_unlink_recomputes_removed_invoice(self):
        partner = self._partner('Borrada')
        self._student(partner)
        self._create_invoice(partner)
        latest = self._create_invoice(partner)
        self.assertTrue(partner.irg_is_moroso)
        # Una factura publicada no se puede borrar. Se deja en borrador por
        # SQL para que el gancho de unlink sea quien quite el marcador.
        self.env.cr.execute(
            "UPDATE account_move SET state = 'draft' WHERE id = %s",
            [latest.id],
        )
        latest.invalidate_recordset(['state'])

        latest.unlink()

        self.assertFalse(partner.irg_is_moroso)
        self.assertTrue(self._notes(partner, 'Deja de ser moroso. Facturas sin pagar: 1.'))

    def test_non_student_partner_has_no_student_note(self):
        partner = self._partner('Solo contacto')
        self._create_invoice(partner)
        self._create_invoice(partner)

        self.assertTrue(partner.irg_is_moroso)
        self.assertFalse(self.env['op.student'].search([('partner_id', '=', partner.id)]))
        self.assertEqual(len(self._notes(partner, 'Pasa a moroso. Facturas sin pagar: 2.')), 1)

    def test_creating_student_applies_linked_invoice_domain(self):
        payer = self._partner('Pagador previo')
        student_partner = self._partner('Alumno posterior')
        self._create_invoice(payer, student_partner=student_partner)
        self._create_invoice(payer, student_partner=student_partner)
        self.assertTrue(payer.irg_is_moroso)
        self.assertFalse(student_partner.irg_is_moroso)

        student = self._student(student_partner)

        self.assertTrue(student_partner.irg_is_moroso)
        self.assertTrue(student.irg_is_moroso)
        self.assertTrue(
            self._notes(student, 'Pasa a moroso. Facturas sin pagar: 2.')
        )

    def test_copied_partner_does_not_keep_the_flag(self):
        partner = self._partner('Original')
        self._create_invoice(partner)
        self._create_invoice(partner)
        self.assertTrue(partner.irg_is_moroso)

        copied = partner.copy()

        self.assertFalse(copied.irg_is_moroso)

    def test_forms_show_lilac_ribbon_only_as_widget(self):
        partner_arch = self.env['res.partner'].get_view(view_type='form')['arch']
        student_arch = self.env['op.student'].get_view(view_type='form')['arch']

        for arch in (partner_arch, student_arch):
            self.assertIn('irg_bg_moroso', arch)
            self.assertIn('title="Moroso"', arch)
            self.assertIn(
                '&quot;irg_is_moroso&quot;, &quot;=&quot;, false',
                arch,
            )

        cron = self.env.ref(
            'irg_moroso_banner.ir_cron_recompute_moroso',
            raise_if_not_found=False,
        )
        self.assertTrue(cron)
        self.assertEqual(cron.name, 'Recalcular morosos')
        self.assertTrue(cron.active)

    def test_paid_dotado_invoice_marks_partner_and_student(self):
        partner = self._partner('Pagada dotada')
        student = self._student(partner)
        invoice = self._create_invoice(partner)
        self._pay(invoice)
        invoice.write({'irg_dotado_morosidad': True})

        self.assertEqual(invoice.payment_state, 'paid')
        self.assertFalse(partner.irg_is_moroso)
        self.assertTrue(partner.irg_is_dotado_morosidad)
        self.assertTrue(student.irg_is_dotado_morosidad)
        notes = self._notes(partner, 'Pasa a dotado por morosidad.')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes.subtype_id, self.env.ref('mail.mt_note'))
        self.assertEqual(len(self._notes(student, 'Pasa a dotado por morosidad.')), 1)

        partner._irg_recompute_dotado()
        self.assertEqual(len(self._notes(partner, 'Pasa a dotado por morosidad.')), 1)

    def test_one_unpaid_dotado_invoice_is_red_not_moroso(self):
        partner = self._partner('Una dotada impagada')
        invoice = self._create_invoice(partner)
        invoice.write({'irg_dotado_morosidad': True})

        self.assertFalse(partner.irg_is_moroso)
        self.assertTrue(partner.irg_is_dotado_morosidad)
        self.assertEqual(len(self._notes(partner, 'Pasa a dotado por morosidad.')), 1)

    def test_two_unpaid_invoices_stay_lilac_only(self):
        partner = self._partner('Solo lila')
        self._student(partner)
        self._create_invoice(partner)
        self._create_invoice(partner)

        self.assertTrue(partner.irg_is_moroso)
        self.assertFalse(partner.irg_is_dotado_morosidad)
        self.assertFalse(self._notes(partner, 'Pasa a dotado por morosidad.'))

    def test_moroso_flag_stays_when_another_invoice_is_dotado(self):
        partner = self._partner('Lila y roja')
        self._create_invoice(partner)
        self._create_invoice(partner)
        paid = self._create_invoice(partner)
        self._pay(paid)
        self.assertTrue(partner.irg_is_moroso)

        paid.write({'irg_dotado_morosidad': True})

        self.assertTrue(partner.irg_is_moroso)
        self.assertTrue(partner.irg_is_dotado_morosidad)

    def test_clearing_dotado_invoice_removes_red_banner(self):
        partner = self._partner('Quitar dotación')
        self._create_invoice(partner)
        self._create_invoice(partner)
        paid = self._create_invoice(partner)
        self._pay(paid)
        paid.write({'irg_dotado_morosidad': True})
        self.assertTrue(partner.irg_is_dotado_morosidad)

        paid.write({'irg_dotado_morosidad': False})

        self.assertFalse(partner.irg_is_dotado_morosidad)
        self.assertTrue(partner.irg_is_moroso)
        self.assertEqual(
            len(self._notes(partner, 'Deja de estar dotado por morosidad.')),
            1,
        )

    def test_payer_and_linked_student_follow_their_own_rule(self):
        payer = self._partner('Pagador dotado')
        student_partner = self._partner('Alumno dotado')
        other = self._partner('Otro hijo')
        student = self._student(student_partner)
        self._student(other)
        invoice = self._create_invoice(payer, student_partner=student_partner)
        invoice.write({'irg_dotado_morosidad': True})

        self.assertTrue(payer.irg_is_dotado_morosidad)
        self.assertTrue(student_partner.irg_is_dotado_morosidad)
        self.assertTrue(student.irg_is_dotado_morosidad)
        self.assertFalse(other.irg_is_dotado_morosidad)

    def test_copied_partner_does_not_keep_dotado_flag(self):
        partner = self._partner('Original dotado')
        invoice = self._create_invoice(partner)
        invoice.write({'irg_dotado_morosidad': True})
        self.assertTrue(partner.irg_is_dotado_morosidad)

        copied = partner.copy()

        self.assertFalse(copied.irg_is_dotado_morosidad)

    def test_silent_recompute_sets_dotado_without_note(self):
        partner = self._partner('Instalación')
        invoice = self._create_invoice(partner)
        invoice.write({'irg_dotado_morosidad': True})
        self.env.cr.execute(
            'UPDATE res_partner SET irg_is_dotado_morosidad = false WHERE id = %s',
            [partner.id],
        )
        partner.invalidate_recordset(['irg_is_dotado_morosidad'])
        before = len(partner.message_ids)

        partner._irg_recompute_dotado(notify=False)

        self.assertTrue(partner.irg_is_dotado_morosidad)
        self.assertEqual(len(partner.message_ids), before)

    def test_forms_show_red_dotado_ribbon(self):
        partner_arch = self.env['res.partner'].get_view(view_type='form')['arch']
        student_arch = self.env['op.student'].get_view(view_type='form')['arch']

        for arch in (partner_arch, student_arch):
            self.assertIn('title="Dotado por morosidad"', arch)
            self.assertIn('bg-danger', arch)
            self.assertIn(
                '&quot;irg_is_dotado_morosidad&quot;, &quot;=&quot;, false',
                arch,
            )
            self.assertIn(
                '&quot;irg_is_dotado_morosidad&quot;, &quot;=&quot;, true',
                arch,
            )
