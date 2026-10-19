# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _IRG_MOROSO_INVOICE_THRESHOLD = 2

    irg_is_moroso = fields.Boolean(
        string='Moroso',
        default=False,
        copy=False,
        index=True,
    )

    def _irg_is_student_partner(self):
        self.ensure_one()
        return bool(self.env['op.student'].sudo().with_context(
            active_test=False
        ).search_count([('partner_id', '=', self.id)]))

    def _irg_unpaid_invoice_domain(self):
        self.ensure_one()
        domain = [
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ('not_paid', 'partial')),
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

    def _irg_unpaid_invoice_count(self):
        self.ensure_one()
        return self.env['account.move'].sudo().search_count(
            self._irg_unpaid_invoice_domain()
        )

    def _irg_partner_should_be_moroso(self):
        self.ensure_one()
        return (
            self._irg_unpaid_invoice_count()
            >= self._IRG_MOROSO_INVOICE_THRESHOLD
        )

    def _irg_moroso_note_author(self):
        user = self.env.user
        if user and not user.share and user.has_group('base.group_user'):
            return user
        return self.env.ref('base.user_root')

    def _irg_post_moroso_note(self, count, becoming_moroso):
        self.ensure_one()
        if becoming_moroso:
            body = _(
                'Pasa a moroso. Facturas sin pagar: %(count)s.',
                count=count,
            )
        else:
            body = _(
                'Deja de ser moroso. Facturas sin pagar: %(count)s.',
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
            count = partner._irg_unpaid_invoice_count()
            partner.sudo().write({'irg_is_moroso': should})
            partner._irg_post_moroso_note(count, should)
        return True

    @api.model
    def _cron_recompute_moroso(self):
        open_invoices = self.env['account.move'].sudo().search([
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])
        partners = self.sudo().with_context(active_test=False).search([
            ('irg_is_moroso', '=', True),
        ])
        partners |= open_invoices.partner_id
        partners |= open_invoices.irg_student_partner_id
        return partners._irg_recompute_moroso()
