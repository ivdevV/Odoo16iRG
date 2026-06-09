# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

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
