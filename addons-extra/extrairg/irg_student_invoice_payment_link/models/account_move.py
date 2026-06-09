# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    _IRG_STUDENT_BACKFILL_BATCH_SIZE = 500

    irg_student_partner_id = fields.Many2one(
        'res.partner',
        string='Alumno',
        compute='_compute_irg_student_partner_id',
        store=True,
        index=True,
        copy=False,
        readonly=True,
    )

    @api.depends('invoice_line_ids.sale_line_ids.order_id.student_id')
    def _compute_irg_student_partner_id(self):
        for move in self:
            sale_orders = move.invoice_line_ids.sale_line_ids.order_id
            students = sale_orders.mapped('student_id')
            move.irg_student_partner_id = students[:1]

    @api.model
    def irg_backfill_student_partner_id(self):
        domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('invoice_line_ids.sale_line_ids.order_id.student_id', '!=', False),
        ]
        move_ids = self.search(domain).ids
        for index in range(0, len(move_ids), self._IRG_STUDENT_BACKFILL_BATCH_SIZE):
            batch = self.browse(
                move_ids[index:index + self._IRG_STUDENT_BACKFILL_BATCH_SIZE]
            )
            batch._compute_irg_student_partner_id()
        return len(move_ids)
