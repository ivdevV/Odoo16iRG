# -*- coding: utf-8 -*-

from datetime import date, datetime, time, timedelta

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestVacation30DayCap(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Leave = cls.env["hr.leave"]
        cls.Employee = cls.env["hr.employee"]
        cls.vacation_type = cls.env.ref(
            "nomina_cfdi_extras_ee.hr_holidays_status_vac", raise_if_not_found=False
        )
        if not cls.vacation_type:
            cls.vacation_type = cls.env["hr.leave.type"].create(
                {"name": "Vacaciones", "requires_allocation": "no"}
            )
            cls.env["ir.model.data"].sudo().create(
                {
                    "module": "nomina_cfdi_extras_ee",
                    "name": "hr_holidays_status_vac",
                    "model": "hr.leave.type",
                    "res_id": cls.vacation_type.id,
                }
            )
        cls.other_type = cls.env["hr.leave.type"].create(
            {"name": "Permiso sin limite", "requires_allocation": "no"}
        )
        cls.employee = cls.Employee.create({"name": "Empleado vacaciones"})
        cls.other_employee = cls.Employee.create({"name": "Otro empleado"})

    def _business_days(self, start, count):
        days = []
        current = start
        while len(days) < count:
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        return days

    def _create_leave(self, employee, leave_type, day, state="validate"):
        leave = self.Leave.create(
            {
                "name": "Ausencia de prueba",
                "employee_id": employee.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": day,
                "request_date_to": day,
                "date_from": datetime.combine(day, time(8, 0)),
                "date_to": datetime.combine(day, time(17, 0)),
            }
        )
        if state == "validate":
            leave.action_validate()
        return leave

    def _create_vacation_days(self, employee, start, count):
        for day in self._business_days(start, count):
            self._create_leave(employee, self.vacation_type, day)

    def test_30_vacation_days_are_allowed(self):
        self._create_vacation_days(self.employee, date(2026, 1, 5), 30)

    def test_31st_vacation_day_is_blocked_on_validation(self):
        days = self._business_days(date(2026, 1, 5), 31)
        leave = self._create_leave(
            self.employee, self.vacation_type, days[30], state="confirm"
        )
        for day in days[:30]:
            self._create_leave(self.employee, self.vacation_type, day)

        with self.assertRaises(UserError):
            leave.action_validate()

    def test_31st_vacation_day_is_blocked_on_create(self):
        days = self._business_days(date(2026, 1, 5), 31)
        for day in days[:30]:
            self._create_leave(self.employee, self.vacation_type, day)

        with self.assertRaises(UserError):
            self._create_leave(
                self.employee, self.vacation_type, days[30], state="confirm"
            )

    def test_write_to_vacation_type_is_blocked_above_limit(self):
        days = self._business_days(date(2026, 1, 5), 31)
        for day in days[:30]:
            self._create_leave(self.employee, self.vacation_type, day)

        leave = self._create_leave(self.employee, self.other_type, days[30])
        with self.assertRaises(UserError):
            leave.write({"holiday_status_id": self.vacation_type.id})

    def test_other_leave_type_is_unaffected(self):
        self._create_vacation_days(self.employee, date(2026, 1, 5), 30)

        self._create_leave(self.employee, self.other_type, date(2026, 3, 2))

    def test_other_employee_is_unaffected(self):
        self._create_vacation_days(self.employee, date(2026, 1, 5), 30)

        self._create_leave(self.other_employee, self.vacation_type, date(2026, 3, 2))

    def test_different_calendar_year_is_unaffected(self):
        self._create_vacation_days(self.employee, date(2026, 1, 5), 30)

        self._create_leave(self.employee, self.vacation_type, date(2027, 1, 4))

    def test_max_leaves_can_be_manually_edited(self):
        self.vacation_type.max_leaves = 30.0

        self.assertTrue(self.vacation_type.irg_use_manual_max_leaves)
        self.assertEqual(self.vacation_type.irg_manual_max_leaves, 30.0)
        self.assertEqual(self.vacation_type.max_leaves, 30.0)
