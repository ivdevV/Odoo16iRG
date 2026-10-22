# -*- coding: utf-8 -*-

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.tools import formatLang


class IrgCuota(object):

    def __init__(self, order, date_due, amount, label, key, kind, schedule_id=0):
        self.order_id = order
        self.date_due = date_due
        self.amount_recurring_taxinc = amount
        self.currency_id = order.currency_id
        self.term_label = label or ''
        self.key = key
        self.kind = kind
        self.schedule_id = schedule_id


class ResPartner(models.Model):
    _inherit = 'res.partner'

    irg_is_moroso = fields.Boolean(
        string='Moroso',
        default=False,
        copy=False,
        index=True,
    )
    irg_moroso_cuota_key = fields.Char(
        string='Cuotas vencidas registradas',
        copy=False,
    )
    irg_is_dotado_morosidad = fields.Boolean(
        string='Dotado por morosidad',
        default=False,
        copy=False,
        index=True,
    )

    def _irg_is_student_partner(self):
        self.ensure_one()
        return bool(self.env['op.student'].sudo().with_context(
            active_test=False
        ).search_count([('partner_id', '=', self.id)]))

    @api.model
    def _irg_moroso_month_start(self):
        today = fields.Date.context_today(self)
        return today.replace(day=1)

    def _irg_partner_orders(self):
        self.ensure_one()
        domain = [('state', 'in', ('sale', 'done'))]
        if self._irg_is_student_partner():
            domain += [
                '|',
                ('partner_id', '=', self.id),
                ('student_id', '=', self.id),
            ]
        else:
            domain.append(('partner_id', '=', self.id))
        return self.env['sale.order'].sudo().search(domain)

    def _irg_order_posted_invoices(self, order):
        moves = self.env['account.move'].sudo()
        if 'order_subscription_id' in moves._fields:
            moves |= moves.search([
                ('order_subscription_id', '=', order.id),
            ])
        moves |= order.order_line.invoice_lines.move_id
        return moves.filtered(
            lambda move: move.state == 'posted' and move.move_type == 'out_invoice'
        )

    def _irg_order_collected(self, order, currency):
        collected = 0.0
        for invoice in self._irg_order_posted_invoices(order):
            collected += (invoice.amount_total or 0.0) - (invoice.amount_residual or 0.0)
        collected = currency.round(collected)
        if currency.compare_amounts(collected, 0.0) < 0:
            return 0.0
        return collected

    def _irg_term_reference_date(self, order):
        if order.start_date:
            return order.start_date
        if order.date_order:
            return fields.Date.to_date(order.date_order)
        return False

    def _irg_term_amounts(self, order):
        currency = order.currency_id or order.company_id.currency_id
        company = order.company_id or self.env.company
        untaxed_currency = order.amount_untaxed or 0.0
        tax_currency = order.amount_tax or 0.0
        if currency and company.currency_id and currency != company.currency_id:
            date_ref = self._irg_term_reference_date(order) or fields.Date.context_today(order)
            untaxed = currency._convert(
                untaxed_currency, company.currency_id, company, date_ref,
            )
            tax = currency._convert(
                tax_currency, company.currency_id, company, date_ref,
            )
        else:
            untaxed = untaxed_currency
            tax = tax_currency
        return currency, company, untaxed, tax, untaxed_currency, tax_currency

    def _irg_term_cuotas(self, order):
        self.ensure_one()
        term = order.payment_term_id
        date_ref = self._irg_term_reference_date(order)
        if not term or not date_ref:
            return []
        currency, company, untaxed, tax, untaxed_currency, tax_currency = (
            self._irg_term_amounts(order)
        )
        terms = term._compute_terms(
            date_ref=date_ref,
            currency=currency,
            company=company,
            tax_amount=tax,
            tax_amount_currency=tax_currency,
            sign=1,
            untaxed_amount=untaxed,
            untaxed_amount_currency=untaxed_currency,
        )
        paid = self._irg_order_collected(order, currency)
        month_start = self._irg_moroso_month_start()
        cuotas = []
        for installment in terms:
            due = fields.Date.to_date(installment.get('date'))
            amount = currency.round(abs(installment.get('foreign_amount') or 0.0))
            if not due or currency.is_zero(amount):
                continue
            covered = amount if currency.compare_amounts(paid, amount) >= 0 else paid
            pending = currency.round(amount - covered)
            paid = currency.round(paid - covered)
            if due < month_start and not currency.is_zero(pending):
                cuotas.append(IrgCuota(
                    order=order,
                    date_due=due,
                    amount=pending,
                    label='',
                    key='term:%s:%s:%.2f' % (order.id, due, pending),
                    kind='term',
                ))
        return cuotas

    def _irg_schedule_cuotas(self, order):
        self.ensure_one()
        schedules = self.env['sale.subscription.schedule'].sudo().search([
            ('order_id', '=', order.id),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('date_due', '<', self._irg_moroso_month_start()),
        ], order='date_due, id')
        return [
            IrgCuota(
                order=order,
                date_due=schedule.date_due,
                amount=schedule.amount_recurring_taxinc or 0.0,
                label=schedule.term_label,
                key=str(schedule.id),
                kind='schedule',
                schedule_id=schedule.id,
            )
            for schedule in schedules
        ]

    def _irg_overdue_cuotas(self):
        self.ensure_one()
        cuotas = []
        for order in self._irg_partner_orders():
            if order.payment_term_id:
                cuotas.extend(self._irg_term_cuotas(order))
            else:
                cuotas.extend(self._irg_schedule_cuotas(order))
        cuotas.sort(key=lambda cuota: (
            cuota.date_due,
            cuota.order_id.id,
            cuota.key,
        ))
        return cuotas

    def _irg_cuota_fingerprint(self, cuotas):
        if cuotas and all(cuota.kind == 'schedule' for cuota in cuotas):
            return ','.join(
                str(cuota.schedule_id)
                for cuota in sorted(cuotas, key=lambda item: item.schedule_id)
            )
        return ','.join(sorted(cuota.key for cuota in cuotas))

    def _irg_overdue_cuota_count(self):
        self.ensure_one()
        return len(self._irg_overdue_cuotas())

    def _irg_partner_should_be_moroso(self):
        self.ensure_one()
        return bool(self._irg_overdue_cuotas())

    def _irg_cuota_line(self, cuota):
        due = cuota.date_due.strftime('%d/%m/%Y') if cuota.date_due else ''
        amount = formatLang(
            self.env,
            cuota.amount_recurring_taxinc or 0.0,
            currency_obj=cuota.currency_id,
        )
        parts = [
            part for part in (
                cuota.order_id.name,
                cuota.term_label,
                due,
                amount,
            ) if part
        ]
        return ' · '.join(parts)

    def _irg_moroso_note_author(self):
        user = self.env.user
        if user and not user.share and user.has_group('base.group_user'):
            return user
        return self.env.ref('base.user_root')

    def _irg_post_moroso_note(self, cuotas, should, was_moroso):
        self.ensure_one()
        count = len(cuotas)
        if should and not was_moroso:
            intro = _(
                'Pasa a moroso. Cuotas vencidas: %(count)s.',
                count=count,
            )
        elif should:
            intro = _('Cuotas vencidas: %(count)s.', count=count)
        else:
            intro = _('Deja de ser moroso. Cuotas vencidas: 0.')
        if should:
            lines = Markup('<br/>').join(
                escape(self._irg_cuota_line(cuota)) for cuota in cuotas
            )
            body = Markup('%s<br/>%s') % (escape(intro), lines)
        else:
            body = intro
        author = self._irg_moroso_note_author()
        post_kwargs = {
            'body': body,
            'subtype_xmlid': 'mail.mt_note',
            'author_id': author.partner_id.id,
        }
        self.sudo().message_post(**post_kwargs)
        students = self.env['op.student'].sudo().with_context(
            active_test=False
        ).search([('partner_id', '=', self.id)])
        for student in students:
            student.sudo().message_post(**post_kwargs)

    def _irg_recompute_moroso(self):
        for partner in self:
            cuotas = partner._irg_overdue_cuotas()
            should = bool(cuotas)
            key = partner._irg_cuota_fingerprint(cuotas)
            if (
                partner.irg_is_moroso == should
                and (partner.irg_moroso_cuota_key or '') == key
            ):
                continue
            was_moroso = partner.irg_is_moroso
            partner.sudo().write({
                'irg_is_moroso': should,
                'irg_moroso_cuota_key': key,
            })
            partner._irg_post_moroso_note(cuotas, should, was_moroso)
        return True

    def _irg_dotado_invoice_domain(self):
        self.ensure_one()
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('irg_dotado_morosidad', '=', True),
        ]
        if self._irg_is_student_partner():
            domain += [
                '|',
                ('partner_id', '=', self.id),
                ('irg_student_partner_id', '=', self.id),
            ]
        else:
            domain.append(('partner_id', '=', self.id))
        return domain

    def _irg_partner_should_be_dotado(self):
        self.ensure_one()
        return bool(self.env['account.move'].sudo().search_count(
            self._irg_dotado_invoice_domain()
        ))

    def _irg_post_dotado_note(self, becoming_dotado):
        self.ensure_one()
        if becoming_dotado:
            body = _('Pasa a dotado por morosidad.')
        else:
            body = _('Deja de estar dotado por morosidad.')
        author = self._irg_moroso_note_author()
        post_kwargs = {
            'body': body,
            'subtype_xmlid': 'mail.mt_note',
            'author_id': author.partner_id.id,
        }
        self.sudo().message_post(**post_kwargs)
        students = self.env['op.student'].sudo().with_context(
            active_test=False
        ).search([('partner_id', '=', self.id)])
        for student in students:
            student.sudo().message_post(**post_kwargs)

    def _irg_recompute_dotado(self, notify=True):
        for partner in self:
            should = partner._irg_partner_should_be_dotado()
            if partner.irg_is_dotado_morosidad == should:
                continue
            partner.sudo().write({'irg_is_dotado_morosidad': should})
            if notify:
                partner._irg_post_dotado_note(should)
        return True

    def _irg_recompute_banners(self):
        self._irg_recompute_moroso()
        self._irg_recompute_dotado()
        return True

    @api.model
    def _irg_recompute_dotado_candidates(self, notify=True):
        invoices = self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('irg_dotado_morosidad', '=', True),
        ])
        partners = self.sudo().with_context(active_test=False).search([
            ('irg_is_dotado_morosidad', '=', True),
        ])
        partners |= invoices.partner_id
        partners |= invoices.irg_student_partner_id
        return partners._irg_recompute_dotado(notify=notify)

    @api.model
    def _cron_recompute_moroso(self):
        month_start = self._irg_moroso_month_start()
        orders = self.env['sale.order'].sudo().search([
            ('state', 'in', ('sale', 'done')),
            ('payment_term_id', '!=', False),
            '|',
            ('start_date', '=', False),
            ('start_date', '<', month_start),
        ])
        schedules = self.env['sale.subscription.schedule'].sudo().search([
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('date_due', '<', month_start),
            ('order_id.state', 'in', ('sale', 'done')),
            ('order_id.payment_term_id', '=', False),
        ])
        partners = self.sudo().with_context(active_test=False).search([
            ('irg_is_moroso', '=', True),
        ])
        partners |= orders.partner_id
        partners |= orders.student_id
        partners |= schedules.order_id.partner_id
        partners |= schedules.order_id.student_id
        partners._irg_recompute_moroso()
        return self._irg_recompute_dotado_candidates(
            notify=not self.env.context.get('irg_dotado_silent')
        )
