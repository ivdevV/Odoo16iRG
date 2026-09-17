# -*- coding: utf-8 -*-
from datetime import date

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_generacion_diplomados_fixed_issue_date')
class TestDiplomadoFixedIssueDate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.course = self.env['op.course'].create({
            'name': 'Diplomado Fecha Fija Test',
            'code': 'DIPFIXDATE',
            'lang': self.env.user.lang or 'en_US',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Alumno Fecha Fija',
        })
        self.student = self.env['op.student'].create({
            'first_name': 'Alumno',
            'last_name': 'Fecha Fija',
            'partner_id': self.partner.id,
        })
        self.env.company.external_report_layout_id = self.env.ref(
            'web.external_layout_standard'
        ).id

    def _expected_issue_date(self):
        today = fields.Date.context_today(self.env.user)
        return date(today.year, 9, 26)

    def _wizard_vals(self, **overrides):
        vals = {
            'student_id': self.student.id,
            'student_name': 'Alumno Fecha Fija',
            'course_id': self.course.id,
            'diplomado_name': self.course.name,
            'duration_hours': 10,
            'diploma_type': 'digital',
        }
        vals.update(overrides)
        return vals

    def _registry_vals(self, **overrides):
        vals = {
            'student_id': self.student.id,
            'student_name': 'Alumno Fecha Fija',
            'course_id': self.course.id,
            'diplomado_name': self.course.name,
            'diploma_type': 'digital',
        }
        vals.update(overrides)
        return vals

    def test_helper_returns_september_26_of_generation_year(self):
        result = self.env['irg.diplomado.registry']._irg_fixed_issue_date()
        self.assertEqual(result, self._expected_issue_date())

    def test_wizard_create_forces_september_26_ignoring_other_date(self):
        wizard = self.env['irg.diplomado.wizard'].create(
            self._wizard_vals(issue_date='2020-01-01')
        )
        self.assertEqual(wizard.issue_date, self._expected_issue_date())

    def test_wizard_write_cannot_keep_another_date(self):
        wizard = self.env['irg.diplomado.wizard'].create(self._wizard_vals())
        wizard.write({'issue_date': '2020-01-01'})
        self.assertEqual(wizard.issue_date, self._expected_issue_date())

    def test_registry_default_is_september_26_of_generation_year(self):
        registry = self.env['irg.diplomado.registry'].create(self._registry_vals())
        self.assertEqual(registry.issue_date, self._expected_issue_date())

    def test_registry_keeps_explicit_issue_date(self):
        registry = self.env['irg.diplomado.registry'].create(
            self._registry_vals(issue_date='2026-06-16')
        )
        self.assertEqual(registry.issue_date, fields.Date.from_string('2026-06-16'))

    def test_print_stores_fixed_issue_date_on_registry(self):
        wizard = self.env['irg.diplomado.wizard'].create(
            self._wizard_vals(issue_date='2020-01-01')
        )
        wizard.action_print_diplomado()
        registry = self.env['irg.diplomado.registry'].search([
            ('student_id', '=', self.student.id),
        ], limit=1)
        self.assertTrue(registry)
        self.assertEqual(registry.issue_date, self._expected_issue_date())
        formatted = self.env['report.irg_generacion_diplomados.diplomado_pdf']._format_issue_date(
            registry.issue_date
        )
        expected_year = self._expected_issue_date().year
        self.assertEqual(formatted, '26 de Septiembre de %s' % expected_year)
