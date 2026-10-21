# -*- coding: utf-8 -*-

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.tools import formatLang


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

    def _irg_overdue_cuota_domain(self):
        self.ensure_one()
        domain = [
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('date_due', '<', self._irg_moroso_month_start()),
            ('order_id.state', 'in', ('sale', 'done')),
        ]
        if self._irg_is_student_partner():
            domain += [
                '|',
                ('order_id.partner_id', '=', self.id),
                ('order_id.student_id', '=', self.id),
            ]
        else:
            domain.append(('order_id.partner_id', '=', self.id))
        return domain

    def _irg_overdue_cuotas(self):
        self.ensure_one()
        return self.env['sale.subscription.schedule'].sudo().search(
            self._irg_overdue_cuota_domain(),
            order='date_due, id',
        )

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
            key = ','.join(str(cuota_id) for cuota_id in sorted(cuotas.ids))
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
        schedules = self.env['sale.subscription.schedule'].sudo().search([
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('date_due', '<', self._irg_moroso_month_start()),
            ('order_id.state', 'in', ('sale', 'done')),
        ])
        partners = self.sudo().with_context(active_test=False).search([
            ('irg_is_moroso', '=', True),
        ])
        partners |= schedules.order_id.partner_id
        partners |= schedules.order_id.student_id
        partners._irg_recompute_moroso()
        return self._irg_recompute_dotado_candidates(
            notify=not self.env.context.get('irg_dotado_silent')
        )
