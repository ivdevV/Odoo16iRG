# -*- coding: utf-8 -*-

import os

from odoo import fields
from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInvoiceDotacionBanner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.income_account = cls.env['account.account'].create({
            'name': 'Test Income IRG Dotacion',
            'code': 'TSTDIN',
            'account_type': 'income',
            'company_id': cls.env.company.id,
        })
        cls.expense_account = cls.env['account.account'].create({
            'name': 'Test Expense IRG Dotacion',
            'code': 'TSTEDT',
            'account_type': 'expense',
            'company_id': cls.env.company.id,
        })
        cls.receivable_account = cls.env['account.account'].create({
            'name': 'Test Receivable IRG Dotacion',
            'code': 'TSTRDT',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'company_id': cls.env.company.id,
        })
        cls.payable_account = cls.env['account.account'].create({
            'name': 'Test Payable IRG Dotacion',
            'code': 'TSTPDT',
            'account_type': 'liability_payable',
            'reconcile': True,
            'company_id': cls.env.company.id,
        })
        cls.sale_journal = cls.env['account.journal'].create({
            'name': 'Test Sales IRG Dotacion',
            'code': 'TSIDT',
            'type': 'sale',
            'company_id': cls.env.company.id,
            'default_account_id': cls.income_account.id,
        })
        cls.purchase_journal = cls.env['account.journal'].create({
            'name': 'Test Purchase IRG Dotacion',
            'code': 'TPIDT',
            'type': 'purchase',
            'company_id': cls.env.company.id,
            'default_account_id': cls.expense_account.id,
        })
        cls.general_journal = cls.env['account.journal'].create({
            'name': 'Test Misc IRG Dotacion',
            'code': 'TSDOT',
            'type': 'general',
            'company_id': cls.env.company.id,
        })
        cls.bank_account = cls.env['account.account'].create({
            'name': 'Test Bank IRG Dotacion',
            'code': 'TSTBDT',
            'account_type': 'asset_cash',
            'company_id': cls.env.company.id,
        })
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Test Bank IRG Dotacion',
            'code': 'TBDOT',
            'type': 'bank',
            'company_id': cls.env.company.id,
            'default_account_id': cls.bank_account.id,
        })
        cls.bank_journal.inbound_payment_method_line_ids.write({
            'payment_account_id': cls.bank_account.id,
        })

    def _partner(self, name):
        return self.env['res.partner'].create({
            'name': name,
            'property_account_receivable_id': self.receivable_account.id,
            'property_account_payable_id': self.payable_account.id,
        })

    def _create_invoice(self, partner, move_type='out_invoice', amount=100.0):
        journal = self.sale_journal
        account = self.income_account
        if move_type == 'in_invoice':
            journal = self.purchase_journal
            account = self.expense_account
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'journal_id': journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Cuota',
                'account_id': account.id,
                'quantity': 1.0,
                'price_unit': amount,
                'tax_ids': [(6, 0, [])],
            })],
        })
        invoice.action_post()
        return invoice

    def _open_line(self, move):
        lines = move.line_ids.filtered(
            lambda line: line.account_id.reconcile and not line.reconciled
        )
        self.assertTrue(lines)
        return lines[0]

    def _create_counterpart(
        self, move, ref='Dotación por morosidad', line_name=None,
        post=True, ratio=1.0,
    ):
        target = self._open_line(move)
        amount = abs(target.amount_residual) * ratio
        label = ref if line_name is None else line_name
        if target.amount_residual > 0:
            target_vals = {'debit': 0.0, 'credit': amount}
            other_vals = {'debit': amount, 'credit': 0.0}
        else:
            target_vals = {'debit': amount, 'credit': 0.0}
            other_vals = {'debit': 0.0, 'credit': amount}
        other_account = (
            self.expense_account
            if target.amount_residual > 0
            else self.income_account
        )
        entry = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.general_journal.id,
            'date': fields.Date.today(),
            'ref': ref,
            'line_ids': [
                (0, 0, dict(other_vals, name=label, account_id=other_account.id)),
                (0, 0, dict(
                    target_vals,
                    name=label,
                    account_id=target.account_id.id,
                    partner_id=move.partner_id.id,
                )),
            ],
        })
        if post:
            entry.action_post()
        return entry

    def _reconcile(self, move, entry):
        target = self._open_line(move)
        counterpart = entry.line_ids.filtered(
            lambda line: line.account_id == target.account_id and not line.reconciled
        )[:1]
        self.assertTrue(counterpart)
        (target | counterpart).reconcile()

    def _notes(self, record, fragment):
        return record.message_ids.filtered(
            lambda message: fragment in (message.body or '')
        )

    def test_unreconciled_invoice_stays_clear_without_note(self):
        invoice = self._create_invoice(self._partner('Sin dotación'))

        self.assertFalse(invoice.irg_dotado_morosidad)
        self.assertFalse(self._notes(invoice, 'Pasa a dotado por morosidad.'))

    def test_reconcile_on_ref_marks_invoice_once(self):
        invoice = self._create_invoice(self._partner('Por referencia'))
        entry = self._create_counterpart(
            invoice, ref='Dotación por morosidad alumnos IRG 31/12/25',
        )
        self._reconcile(invoice, entry)

        self.assertTrue(invoice.irg_dotado_morosidad)
        self.assertFalse(entry.irg_dotado_morosidad)
        notes = self._notes(invoice, 'Pasa a dotado por morosidad.')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes.subtype_id, self.env.ref('mail.mt_note'))

        invoice._irg_recompute_dotacion()
        self.assertEqual(len(self._notes(invoice, 'Pasa a dotado por morosidad.')), 1)

    def test_line_label_alone_marks_invoice(self):
        invoice = self._create_invoice(self._partner('Por etiqueta'))
        entry = self._create_counterpart(
            invoice,
            ref='Asiento manual',
            line_name='Dotación por morosidad alumnos',
        )
        self._reconcile(invoice, entry)

        self.assertTrue(invoice.irg_dotado_morosidad)
        self.assertEqual(len(self._notes(invoice, 'Pasa a dotado por morosidad.')), 1)

    def test_phrase_is_case_insensitive_and_accent_sensitive(self):
        upper = self._create_invoice(self._partner('Mayúsculas'))
        upper_entry = self._create_counterpart(
            upper, ref='DOTACIÓN POR MOROSIDAD',
        )
        self._reconcile(upper, upper_entry)
        self.assertTrue(upper.irg_dotado_morosidad)

        plain = self._create_invoice(self._partner('Sin tilde'))
        plain_entry = self._create_counterpart(
            plain, ref='Dotacion por morosidad',
        )
        self._reconcile(plain, plain_entry)
        self.assertFalse(plain.irg_dotado_morosidad)
        self.assertFalse(self._notes(plain, 'Pasa a dotado por morosidad.'))

    def test_partial_reconcile_counts(self):
        invoice = self._create_invoice(self._partner('Parcial'))
        entry = self._create_counterpart(invoice, ratio=0.4)
        self._reconcile(invoice, entry)

        self.assertEqual(invoice.payment_state, 'partial')
        self.assertTrue(invoice.irg_dotado_morosidad)

    def test_ordinary_payment_does_not_mark(self):
        invoice = self._create_invoice(self._partner('Pago normal'))
        register = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create({
            'journal_id': self.bank_journal.id,
            'payment_date': fields.Date.today(),
        })
        register.action_create_payments()
        invoice.invalidate_recordset()

        self.assertEqual(invoice.payment_state, 'paid')
        self.assertFalse(invoice.irg_dotado_morosidad)
        self.assertFalse(self._notes(invoice, 'Pasa a dotado por morosidad.'))

    def test_unreconcile_clears_flag_and_notes_once(self):
        invoice = self._create_invoice(self._partner('Desconciliar'))
        entry = self._create_counterpart(invoice)
        self._reconcile(invoice, entry)
        self.assertTrue(invoice.irg_dotado_morosidad)

        invoice.line_ids.filtered(
            lambda line: line.account_id == self.receivable_account
        ).remove_move_reconcile()

        self.assertFalse(invoice.irg_dotado_morosidad)
        self.assertEqual(
            len(self._notes(invoice, 'Deja de estar dotado por morosidad.')),
            1,
        )

    def test_reset_to_draft_clears_flag_once(self):
        invoice = self._create_invoice(self._partner('Borrador'))
        entry = self._create_counterpart(invoice)
        self._reconcile(invoice, entry)

        entry.button_draft()

        self.assertFalse(invoice.irg_dotado_morosidad)
        self.assertEqual(
            len(self._notes(invoice, 'Deja de estar dotado por morosidad.')),
            1,
        )

    def test_draft_counterpart_does_not_count(self):
        invoice = self._create_invoice(self._partner('Asiento en borrador'))
        entry = self._create_counterpart(invoice)
        self._reconcile(invoice, entry)
        self.env.cr.execute(
            "UPDATE account_move SET state = 'draft' WHERE id = %s",
            [entry.id],
        )
        entry.invalidate_recordset(['state'])
        invoice.line_ids.invalidate_recordset(['parent_state'])

        invoice._irg_recompute_dotacion()

        self.assertFalse(invoice.irg_dotado_morosidad)
        self.assertEqual(
            len(self._notes(invoice, 'Deja de estar dotado por morosidad.')),
            1,
        )

    def test_clearing_ref_and_label_clears_flag(self):
        invoice = self._create_invoice(self._partner('Cambia el texto'))
        entry = self._create_counterpart(
            invoice,
            ref='Dotación por morosidad alumnos',
            line_name='Dotación por morosidad alumnos',
        )
        self._reconcile(invoice, entry)
        self.assertTrue(invoice.irg_dotado_morosidad)

        entry.write({'ref': 'Asiento ordinario'})
        self.assertTrue(invoice.irg_dotado_morosidad)
        self.assertFalse(self._notes(invoice, 'Deja de estar dotado por morosidad.'))

        entry.line_ids.write({'name': 'Asiento ordinario'})
        self.assertFalse(invoice.irg_dotado_morosidad)
        self.assertEqual(
            len(self._notes(invoice, 'Deja de estar dotado por morosidad.')),
            1,
        )

    def test_adding_label_after_reconcile_marks_invoice(self):
        invoice = self._create_invoice(self._partner('Etiqueta posterior'))
        entry = self._create_counterpart(
            invoice, ref='Asiento ordinario', line_name='Asiento ordinario',
        )
        self._reconcile(invoice, entry)
        self.assertFalse(invoice.irg_dotado_morosidad)

        counterpart = entry.line_ids.filtered(
            lambda line: line.account_id == self.receivable_account
        )
        counterpart.write({'name': 'Dotación por morosidad'})

        self.assertTrue(invoice.irg_dotado_morosidad)
        self.assertEqual(len(self._notes(invoice, 'Pasa a dotado por morosidad.')), 1)

    def test_several_lines_post_a_single_note(self):
        invoice = self._create_invoice(self._partner('Varias líneas'))
        entry = self._create_counterpart(
            invoice,
            ref='Dotación por morosidad',
            line_name='Dotación por morosidad',
        )
        self._reconcile(invoice, entry)

        self.assertEqual(len(self._notes(invoice, 'Pasa a dotado por morosidad.')), 1)

    def test_one_entry_marks_each_invoice(self):
        first = self._create_invoice(self._partner('Factura uno'), amount=40.0)
        second = self._create_invoice(self._partner('Factura dos'), amount=60.0)
        first_line = self._open_line(first)
        second_line = self._open_line(second)
        entry = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': self.general_journal.id,
            'date': fields.Date.today(),
            'ref': 'Dotación por morosidad alumnos',
            'line_ids': [
                (0, 0, {
                    'name': 'Dotación por morosidad alumnos',
                    'account_id': self.expense_account.id,
                    'debit': 100.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Dotación por morosidad alumnos',
                    'account_id': first_line.account_id.id,
                    'partner_id': first.partner_id.id,
                    'debit': 0.0,
                    'credit': 40.0,
                }),
                (0, 0, {
                    'name': 'Dotación por morosidad alumnos',
                    'account_id': second_line.account_id.id,
                    'partner_id': second.partner_id.id,
                    'debit': 0.0,
                    'credit': 60.0,
                }),
            ],
        })
        entry.action_post()
        self._reconcile(first, entry)
        self._reconcile(second, entry)

        self.assertTrue(first.irg_dotado_morosidad)
        self.assertTrue(second.irg_dotado_morosidad)
        self.assertFalse(entry.irg_dotado_morosidad)
        self.assertEqual(len(self._notes(first, 'Pasa a dotado por morosidad.')), 1)
        self.assertEqual(len(self._notes(second, 'Pasa a dotado por morosidad.')), 1)

    def test_refund_and_vendor_bill_stay_clear(self):
        partner = self._partner('Otros documentos')
        refund = self._create_invoice(partner, move_type='out_refund')
        refund_entry = self._create_counterpart(refund)
        self._reconcile(refund, refund_entry)
        bill = self._create_invoice(partner, move_type='in_invoice')
        bill_entry = self._create_counterpart(bill)
        self._reconcile(bill, bill_entry)

        self.assertFalse(refund.irg_dotado_morosidad)
        self.assertFalse(bill.irg_dotado_morosidad)
        self.assertFalse(refund_entry.irg_dotado_morosidad)
        self.assertFalse(bill_entry.irg_dotado_morosidad)

    def test_copy_does_not_keep_the_flag(self):
        invoice = self._create_invoice(self._partner('Duplicada'))
        entry = self._create_counterpart(invoice)
        self._reconcile(invoice, entry)
        self.assertTrue(invoice.irg_dotado_morosidad)

        copied = invoice.copy()

        self.assertFalse(copied.irg_dotado_morosidad)

    def test_install_recompute_sets_flag_without_note(self):
        invoice = self._create_invoice(self._partner('Ya conciliada'))
        entry = self._create_counterpart(invoice)
        self._reconcile(invoice, entry)
        self.env.cr.execute(
            'UPDATE account_move SET irg_dotado_morosidad = false WHERE id = %s',
            [invoice.id],
        )
        invoice.invalidate_recordset(['irg_dotado_morosidad'])
        before = len(invoice.message_ids)

        self.env['account.move']._irg_install_recompute_dotacion()

        self.assertTrue(invoice.irg_dotado_morosidad)
        self.assertEqual(len(invoice.message_ids), before)

    def test_form_shows_dotacion_ribbon(self):
        arch = self.env['account.move'].get_view(view_type='form')['arch']
        self.assertIn('title="Dotado por morosidad"', arch)
        self.assertIn('irg_bg_dotado', arch)
        self.assertIn(
            '&quot;irg_dotado_morosidad&quot;, &quot;=&quot;, false',
            arch,
        )
        scss_path = os.path.join(
            get_module_path('irg_invoice_dotacion_banner'),
            'static', 'src', 'scss', 'dotacion_ribbon.scss',
        )
        with open(scss_path, encoding='utf-8') as handle:
            scss = handle.read()
        self.assertIn('#4F6D7A', scss)
        self.assertIn('#FFFFFF', scss)
        self.assertIn('.ribbon span.irg_bg_dotado', scss)
