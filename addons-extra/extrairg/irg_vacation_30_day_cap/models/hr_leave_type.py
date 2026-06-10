# -*- coding: utf-8 -*-

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    max_leaves = fields.Float(
        compute="_compute_leaves",
        inverse="_inverse_irg_manual_max_leaves",
        readonly=False,
    )
    irg_manual_max_leaves = fields.Float(string="iRG Manual Maximum Allowed")
    irg_use_manual_max_leaves = fields.Boolean(string="iRG Use Manual Maximum Allowed")

    def _compute_leaves(self):
        super()._compute_leaves()
        for leave_type in self:
            if leave_type.irg_use_manual_max_leaves:
                leave_type.max_leaves = leave_type.irg_manual_max_leaves
                leave_type.remaining_leaves = (
                    leave_type.irg_manual_max_leaves - leave_type.leaves_taken
                )
                leave_type.virtual_remaining_leaves = (
                    leave_type.irg_manual_max_leaves - leave_type.virtual_leaves_taken
                )

    def _inverse_irg_manual_max_leaves(self):
        for leave_type in self:
            leave_type.irg_manual_max_leaves = leave_type.max_leaves
            leave_type.irg_use_manual_max_leaves = True
