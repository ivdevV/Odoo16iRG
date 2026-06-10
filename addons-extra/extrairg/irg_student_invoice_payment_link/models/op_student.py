# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class OpStudent(models.Model):
    _inherit = 'op.student'

    irg_invoice_count = fields.Integer(
        string='Facturas academicas',
        compute='_compute_irg_invoice_payment_count',
    )
    irg_payment_count = fields.Integer(
        string='Pagos',
        compute='_compute_irg_invoice_payment_count',
    )

    def _get_irg_academic_invoice_domain(self):
        self.ensure_one()
        return [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            '|',
            ('partner_id', '=', self.partner_id.id),
            ('irg_student_partner_id', '=', self.partner_id.id),
        ]

    def _get_irg_academic_invoices(self):
        self.ensure_one()
        return self.env['account.move'].search(
            self._get_irg_academic_invoice_domain()
        )

    def _get_irg_academic_payments(self):
        self.ensure_one()
        invoices = self._get_irg_academic_invoices()
        return invoices._get_reconciled_payments()

    @api.depends('partner_id')
    def _compute_irg_invoice_payment_count(self):
        for student in self:
            if not student.partner_id:
                student.irg_invoice_count = 0
                student.irg_payment_count = 0
                continue
            invoices = student._get_irg_academic_invoices()
            student.irg_invoice_count = len(invoices)
            student.irg_payment_count = len(invoices._get_reconciled_payments())

    def action_view_invoice(self):
        self.ensure_one()
        result = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_move_out_invoice_type'
        )
        invoices = self._get_irg_academic_invoices()
        result['domain'] = [('id', 'in', invoices.ids)]
        result['context'] = {
            'default_move_type': 'out_invoice',
            'default_partner_id': self.partner_id.id,
        }
        if len(invoices) == 1:
            form_view = self.env.ref('account.view_move_form', raise_if_not_found=False)
            result['views'] = [(form_view.id if form_view else False, 'form')]
            result['res_id'] = invoices.id
        return result

    def action_view_academic_payments(self):
        self.ensure_one()
        payments = self._get_irg_academic_payments()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Pagos'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payments.ids)],
            'context': {'create': False},
            'target': 'current',
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        return action
