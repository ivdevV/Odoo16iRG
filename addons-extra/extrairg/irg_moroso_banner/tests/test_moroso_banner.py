# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

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
            'course_type': 'none',
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
                        amount=100.0, student_partner=None, schedule=None):
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'journal_id': self.sale_journal.id,
            'invoice_date': fields.Date.today(),
            'schedule_id': schedule.id if schedule else False,
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

    def _dates(self):
        today = fields.Date.context_today(self.env.user)
        month_start = today.replace(day=1)
        return month_start, month_start - relativedelta(days=1)

    def _order(self, partner, student=None, confirmed=True):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'student_id': student.id if student else False,
        })
        if confirmed:
            self.env.cr.execute(
                "UPDATE sale_order SET state = 'sale' WHERE id = %s",
                [order.id],
            )
            order.invalidate_recordset(['state'])
        return order

    def _cuota(self, order, date_due, payment_state='not_paid'):
        values = {
            'order_id': order.id,
            'date_due': date_due,
            'date_schedule': date_due,
            'amount_recurring_taxinc': 100.0,
        }
        if payment_state == 'not_paid':
            return self.env['sale.subscription.schedule'].create(values)
        month_start, _previous = self._dates()
        values['date_due'] = month_start
        schedule = self.env['sale.subscription.schedule'].create(values)
        schedule.write({
            'date_due': date_due,
            'payment_state': payment_state,
        })
        return schedule

    def test_two_invoices_do_not_mark_without_overdue_cuota(self):
        partner = self._partner('Dos facturas')
        student = self._student(partner)
        self._create_invoice(partner)
        self._create_invoice(partner)

        self.assertFalse(partner.irg_is_moroso)
        self.assertFalse(student.irg_is_moroso)
        self.assertFalse(self._notes(partner, 'Pasa a moroso'))

    def test_overdue_cuota_marks_partner_and_student(self):
        partner = self._partner('Cuota vencida')
        student = self._student(partner)
        _, previous = self._dates()
        order = self._order(partner)
        self._cuota(order, previous)

        self.assertTrue(partner.irg_is_moroso)
        self.assertTrue(student.irg_is_moroso)
        notes = self._notes(partner, 'Pasa a moroso. Cuotas vencidas: 1.')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes.subtype_id, self.env.ref('mail.mt_note'))
        self.assertEqual(len(self._notes(student, 'Pasa a moroso. Cuotas vencidas: 1.')), 1)

        partner._irg_recompute_moroso()
        self.env['res.partner']._cron_recompute_moroso()
        self.assertEqual(len(self._notes(partner, 'Pasa a moroso. Cuotas vencidas: 1.')), 1)

    def test_partial_overdue_cuota_counts(self):
        partner = self._partner('Cuota parcial')
        _, previous = self._dates()
        order = self._order(partner)
        cuota = self._cuota(order, previous, payment_state='partial')

        self.assertEqual(cuota.payment_state, 'partial')
        self.assertTrue(partner.irg_is_moroso)
        self.assertTrue(self._notes(partner, 'Pasa a moroso. Cuotas vencidas: 1.'))

    def test_current_paid_cancelled_and_draft_cuotas_do_not_count(self):
        partner = self._partner('Cuotas excluidas')
        month_start, previous = self._dates()
        order = self._order(partner)
        self._cuota(order, month_start)
        self._cuota(order, previous, payment_state='paid')
        self._cuota(order, previous, payment_state='cancel')
        draft = self._order(partner, confirmed=False)
        self._cuota(draft, previous)

        self.assertFalse(partner.irg_is_moroso)
        self.assertFalse(self._notes(partner, 'Pasa a moroso'))

    def test_oficialidad_and_master_cuotas_add_up(self):
        partner = self._partner('Dos programas')
        _, previous = self._dates()
        first = self._order(partner, confirmed=False)
        second = self._order(partner, confirmed=False)
        self._cuota(first, previous)
        self._cuota(second, previous)
        self.assertFalse(partner.irg_is_moroso)

        (first | second).write({'state': 'sale'})

        self.assertTrue(partner.irg_is_moroso)
        self.assertEqual(len(self._notes(partner, 'Pasa a moroso. Cuotas vencidas: 2.')), 1)

    def test_payer_and_student_follow_the_order_link(self):
        payer = self._partner('Pagador cuotas')
        student_partner = self._partner('Alumno cuotas')
        other = self._partner('Otro alumno')
        student = self._student(student_partner)
        self._student(other)
        _, previous = self._dates()
        self._cuota(self._order(payer, student=student_partner), previous)

        self.assertTrue(payer.irg_is_moroso)
        self.assertTrue(student_partner.irg_is_moroso)
        self.assertTrue(student.irg_is_moroso)
        self.assertFalse(other.irg_is_moroso)
        self.assertEqual(len(self._notes(payer, 'Pasa a moroso. Cuotas vencidas: 1.')), 1)
        self.assertFalse(self._notes(other, 'Pasa a moroso'))

    def test_paying_overdue_cuota_clears_flag(self):
        partner = self._partner('Paga la cuota')
        student = self._student(partner)
        _, previous = self._dates()
        cuota = self._cuota(self._order(partner), previous)
        self.assertTrue(partner.irg_is_moroso)

        cuota.write({'payment_state': 'paid'})

        self.assertFalse(partner.irg_is_moroso)
        self.assertEqual(
            len(self._notes(partner, 'Deja de ser moroso. Cuotas vencidas: 0.')),
            1,
        )
        self.assertEqual(
            len(self._notes(student, 'Deja de ser moroso. Cuotas vencidas: 0.')),
            1,
        )

    def test_paying_linked_invoice_clears_flag(self):
        partner = self._partner('Cobra la factura')
        _, previous = self._dates()
        cuota = self._cuota(self._order(partner), previous)
        self.assertTrue(partner.irg_is_moroso)
        invoice = self._create_invoice(partner, schedule=cuota)
        self.assertEqual(cuota.payment_state, 'not_paid')

        self._pay(invoice)

        self.assertEqual(cuota.payment_state, 'paid')
        self.assertFalse(partner.irg_is_moroso)
        self.assertEqual(
            len(self._notes(partner, 'Deja de ser moroso. Cuotas vencidas: 0.')),
            1,
        )

    def test_moving_due_date_into_current_month_clears_flag(self):
        partner = self._partner('Cambia el mes')
        month_start, previous = self._dates()
        cuota = self._cuota(self._order(partner), previous)
        self.assertTrue(partner.irg_is_moroso)

        cuota.write({'date_due': month_start})

        self.assertFalse(partner.irg_is_moroso)
        self.assertTrue(self._notes(partner, 'Deja de ser moroso. Cuotas vencidas: 0.'))

    def test_confirming_the_order_starts_counting(self):
        partner = self._partner('Pedido en borrador')
        _, previous = self._dates()
        order = self._order(partner, confirmed=False)
        self._cuota(order, previous)
        self.assertFalse(partner.irg_is_moroso)

        order.write({'state': 'sale'})

        self.assertTrue(partner.irg_is_moroso)
        self.assertTrue(self._notes(partner, 'Pasa a moroso. Cuotas vencidas: 1.'))

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

    def test_two_unpaid_invoices_are_not_moroso(self):
        partner = self._partner('Solo facturas')
        self._student(partner)
        self._create_invoice(partner)
        self._create_invoice(partner)

        self.assertFalse(partner.irg_is_moroso)
        self.assertFalse(partner.irg_is_dotado_morosidad)
        self.assertFalse(self._notes(partner, 'Pasa a dotado por morosidad.'))

    def test_moroso_flag_stays_when_another_invoice_is_dotado(self):
        partner = self._partner('Lila y roja')
        _, previous = self._dates()
        self._cuota(self._order(partner), previous)
        paid = self._create_invoice(partner)
        self._pay(paid)
        self.assertTrue(partner.irg_is_moroso)

        paid.write({'irg_dotado_morosidad': True})

        self.assertTrue(partner.irg_is_moroso)
        self.assertTrue(partner.irg_is_dotado_morosidad)

    def test_clearing_dotado_invoice_removes_red_banner(self):
        partner = self._partner('Quitar dotación')
        _, previous = self._dates()
        self._cuota(self._order(partner), previous)
        paid = self._create_invoice(partner)
        self._pay(paid)
        paid.write({'irg_dotado_morosidad': True})
        self.assertTrue(partner.irg_is_dotado_morosidad)
        self.assertTrue(partner.irg_is_moroso)

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
