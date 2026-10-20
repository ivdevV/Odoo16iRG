# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    _IRG_DOTACION_PHRASE = 'dotación por morosidad'
    _IRG_DOTACION_TRIGGER_FIELDS = frozenset({'state', 'ref'})

    irg_dotado_morosidad = fields.Boolean(
        string='Dotado por morosidad',
        default=False,
        copy=False,
        index=True,
    )

    def _irg_text_has_dotacion_phrase(self, text):
        return self._IRG_DOTACION_PHRASE in (text or '').lower()

    def _irg_partials_of_lines(self, lines):
        if not lines:
            return self.env['account.partial.reconcile']
        return self.env['account.partial.reconcile'].sudo().search([
            '|',
            ('debit_move_id', 'in', lines.ids),
            ('credit_move_id', 'in', lines.ids),
        ])

    def _irg_move_is_dotado_morosidad(self):
        self.ensure_one()
        if self.move_type != 'out_invoice':
            return False
        own_line_ids = set(self.line_ids.ids)
        if not own_line_ids:
            return False
        for partial in self._irg_partials_of_lines(self.line_ids):
            for line in (partial.debit_move_id, partial.credit_move_id):
                if line.id in own_line_ids or line.move_id.state != 'posted':
                    continue
                if (
                    self._irg_text_has_dotacion_phrase(line.move_id.ref)
                    or self._irg_text_has_dotacion_phrase(line.name)
                ):
                    return True
        return False

    def _irg_customer_invoices_reconciled_with(self):
        partials = self._irg_partials_of_lines(self.line_ids)
        moves = partials.debit_move_id.move_id | partials.credit_move_id.move_id
        return moves.filtered(lambda move: move.move_type == 'out_invoice')

    def _irg_post_dotacion_note(self, becoming_dotado):
        self.ensure_one()
        if becoming_dotado:
            body = _('Pasa a dotado por morosidad.')
        else:
            body = _('Deja de estar dotado por morosidad.')
        user = self.env.user
        if not user or user.share or not user.has_group('base.group_user'):
            user = self.env.ref('base.user_root')
        self.sudo().message_post(
            body=body,
            subtype_xmlid='mail.mt_note',
            author_id=user.partner_id.id,
        )

    def _irg_recompute_dotacion(self, notify=True):
        for move in self:
            should = move._irg_move_is_dotado_morosidad()
            if should == move.irg_dotado_morosidad:
                continue
            move.sudo().write({'irg_dotado_morosidad': should})
            if notify:
                move._irg_post_dotacion_note(should)

    @api.model
    def _irg_install_recompute_dotacion(self):
        phrase = self._IRG_DOTACION_PHRASE
        lines = self.env['account.move.line'].sudo().search([
            ('move_id.state', '=', 'posted'),
            '|',
            ('move_id.ref', 'ilike', phrase),
            ('name', 'ilike', phrase),
        ])
        invoices = self.browse()
        if lines:
            partials = self.env['account.partial.reconcile'].sudo().search([
                '|',
                ('debit_move_id', 'in', lines.ids),
                ('credit_move_id', 'in', lines.ids),
            ])
            moves = partials.debit_move_id.move_id | partials.credit_move_id.move_id
            invoices = moves.filtered(lambda move: move.move_type == 'out_invoice')
        flagged = self.sudo().search([('irg_dotado_morosidad', '=', True)])
        (invoices | flagged)._irg_recompute_dotacion(notify=False)

    def write(self, vals):
        result = super().write(vals)
        if self._IRG_DOTACION_TRIGGER_FIELDS.intersection(vals):
            invoices = self.filtered(lambda move: move.move_type == 'out_invoice')
            invoices |= self._irg_customer_invoices_reconciled_with()
            invoices._irg_recompute_dotacion()
        return result


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def write(self, vals):
        result = super().write(vals)
        if 'name' in vals:
            partials = self.env['account.move']._irg_partials_of_lines(self)
            moves = partials.debit_move_id.move_id | partials.credit_move_id.move_id
            moves.filtered(
                lambda move: move.move_type == 'out_invoice'
            )._irg_recompute_dotacion()
        return result


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def _irg_dotacion_invoices(self):
        moves = self.debit_move_id.move_id | self.credit_move_id.move_id
        return moves.filtered(lambda move: move.move_type == 'out_invoice')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_dotacion_invoices()._irg_recompute_dotacion()
        return records

    def unlink(self):
        invoices = self._irg_dotacion_invoices()
        result = super().unlink()
        invoices.exists()._irg_recompute_dotacion()
        return result
