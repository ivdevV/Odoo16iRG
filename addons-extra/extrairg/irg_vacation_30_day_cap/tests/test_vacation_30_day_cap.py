# -*- coding: utf-8 -*-

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestVacation30DayCap(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Leave = cls.env["hr.leave"]
        cls.Employee = cls.env["hr.employee"]
        cls.vacation_type = cls.env.ref("nomina_cfdi_extras_ee.hr_holidays_status_vac")
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
        return self.Leave.create(
            {
                "name": "Ausencia de prueba",
                "employee_id": employee.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": day,
                "request_date_to": day,
                "state": state,
            }
        )

    def _create_vacation_days(self, employee, start, count):
        for day in self._business_days(start, count):
            self._create_leave(employee, self.vacation_type, day)

    def test_30_vacation_days_are_allowed(self):
        self._create_vacation_days(self.employee, date(2026, 1, 5), 30)

    def test_31st_vacation_day_is_blocked_on_validation(self):
        days = self._business_days(date(2026, 1, 5), 31)
        for day in days[:30]:
            self._create_leave(self.employee, self.vacation_type, day)

        leave = self._create_leave(
            self.employee, self.vacation_type, days[30], state="confirm"
        )
        with self.assertRaises(UserError):
            leave.action_validate()

    def test_31st_validated_vacation_day_is_blocked_on_create(self):
        days = self._business_days(date(2026, 1, 5), 31)
        for day in days[:30]:
            self._create_leave(self.employee, self.vacation_type, day)

        with self.assertRaises(UserError):
            self._create_leave(self.employee, self.vacation_type, days[30])

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
