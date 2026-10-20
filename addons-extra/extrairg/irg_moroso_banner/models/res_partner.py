# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    irg_is_moroso = fields.Boolean(
        string='Moroso',
        default=False,
        copy=False,
        index=True,
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

    def _irg_overdue_cuota_count(self):
        self.ensure_one()
        return self.env['sale.subscription.schedule'].sudo().search_count(
            self._irg_overdue_cuota_domain()
        )

    def _irg_partner_should_be_moroso(self):
        self.ensure_one()
        return self._irg_overdue_cuota_count() >= 1

    def _irg_moroso_note_author(self):
        user = self.env.user
        if user and not user.share and user.has_group('base.group_user'):
            return user
        return self.env.ref('base.user_root')

    def _irg_post_moroso_note(self, count, becoming_moroso):
        self.ensure_one()
        if becoming_moroso:
            body = _(
                'Pasa a moroso. Cuotas vencidas: %(count)s.',
                count=count,
            )
        else:
            body = _(
                'Deja de ser moroso. Cuotas vencidas: %(count)s.',
                count=count,
            )
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
            should = partner._irg_partner_should_be_moroso()
            if partner.irg_is_moroso == should:
                continue
            count = partner._irg_overdue_cuota_count()
            partner.sudo().write({'irg_is_moroso': should})
            partner._irg_post_moroso_note(count, should)
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
