# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    IRG_VACATION_CAP_DAYS = 30.0
    IRG_VALIDATED_STATES = ("validate", "validate1")

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        leaves._irg_check_vacation_30_day_cap()
        return leaves

    def write(self, vals):
        result = super().write(vals)
        self._irg_check_vacation_30_day_cap()
        return result

    def action_approve(self):
        self._irg_check_vacation_30_day_cap(include_current=True)
        return super().action_approve()

    def action_validate(self):
        self._irg_check_vacation_30_day_cap(include_current=True)
        return super().action_validate()

    def _irg_check_vacation_30_day_cap(self, include_current=False):
        vacation_type = self.env.ref("nomina_cfdi_extras_ee.hr_holidays_status_vac")
        leaves = self.filtered(
            lambda leave: leave.employee_id and leave.holiday_status_id == vacation_type
        )
        if not include_current:
            leaves = leaves.filtered(lambda leave: leave.state in self.IRG_VALIDATED_STATES)
        if not leaves:
            return

        employee_ids = leaves.employee_id.ids
        years = set()
        for leave in leaves:
            years.update(leave._irg_vacation_years())
        if not years:
            return

        domain = [
            ("id", "not in", leaves.ids),
            ("employee_id", "in", employee_ids),
            ("holiday_status_id", "=", vacation_type.id),
            ("state", "in", self.IRG_VALIDATED_STATES),
            ("request_date_from", "<=", date(max(years), 12, 31)),
            ("request_date_to", ">=", date(min(years), 1, 1)),
        ]
        existing_leaves = self.search(domain)
        totals = defaultdict(float)
        for leave in existing_leaves | leaves:
            for year in leave._irg_vacation_years():
                if year in years:
                    totals[(leave.employee_id.id, year)] += (
                        leave._irg_vacation_days_in_year(year)
                    )

        for (employee_id, year), total in totals.items():
            if total > self.IRG_VACATION_CAP_DAYS:
                employee = self.env["hr.employee"].browse(employee_id)
                raise UserError(
                    _(
                        "El empleado %(employee)s no puede exceder el limite anual "
                        "de %(limit)s dias de vacaciones en el ano %(year)s."
                    )
                    % {
                        "employee": employee.name,
                        "limit": int(self.IRG_VACATION_CAP_DAYS),
                        "year": year,
                    }
                )

    def _irg_vacation_years(self):
        self.ensure_one()
        date_from = fields.Date.to_date(self.request_date_from)
        date_to = fields.Date.to_date(self.request_date_to)
        if not date_from or not date_to:
            return []
        return range(date_from.year, date_to.year + 1)

    def _irg_vacation_days_in_year(self, year):
        self.ensure_one()
        date_from = fields.Date.to_date(self.request_date_from)
        date_to = fields.Date.to_date(self.request_date_to)
        if not date_from or not date_to:
            return self.number_of_days or 0.0

        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        overlap_start = max(date_from, year_start)
        overlap_end = min(date_to, year_end)
        if overlap_start > overlap_end:
            return 0.0

        if date_from.year == date_to.year and self.number_of_days:
            return self.number_of_days

        overlap_days = (overlap_end - overlap_start).days + 1
        return float(overlap_days)
