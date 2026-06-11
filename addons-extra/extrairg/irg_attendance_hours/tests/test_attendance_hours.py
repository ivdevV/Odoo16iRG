# -*- coding: utf-8 -*-

from datetime import datetime
from odoo.tests import common
from odoo.fields import Datetime


class TestAttendanceHours(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAttendanceHours, cls).setUpClass()
        # Creamos los empleados de prueba
        cls.employee_1 = cls.env['hr.employee'].create({
            'name': 'Empleado Test 1',
        })
        cls.employee_2 = cls.env['hr.employee'].create({
            'name': 'Empleado Test 2',
        })

    def test_01_weekly_and_monthly_calculation(self):
        """Prueba que las horas semanales y mensuales se sumen correctamente para un mismo empleado en el mismo periodo."""
        
        # Asistencias de la misma semana y mes (Junio 2026) para Employee 1
        # Semana del lunes 15 de junio al domingo 21 de junio del 2026
        # Lunes 15 de Junio: 8 horas (08:00 a 16:00)
        attendance_1 = self.env['hr.attendance'].create({
            'employee_id': self.employee_1.id,
            'check_in': datetime(2026, 6, 15, 8, 0, 0),
            'check_out': datetime(2026, 6, 15, 16, 0, 0),
        })
        
        # Martes 16 de Junio: 4 horas (08:00 a 12:00)
        attendance_2 = self.env['hr.attendance'].create({
            'employee_id': self.employee_1.id,
            'check_in': datetime(2026, 6, 16, 8, 0, 0),
            'check_out': datetime(2026, 6, 16, 12, 0, 0),
        })

        # Forzar guardado en base de datos para que read_group lo lea
        self.env.flush_all()

        # Verificar sumas semanales (8 + 4 = 12 horas)
        self.assertAlmostEqual(attendance_1.irg_weekly_hours_total, 12.0, places=2)
        self.assertAlmostEqual(attendance_2.irg_weekly_hours_total, 12.0, places=2)
        
        # Verificar sumas mensuales (8 + 4 = 12 horas ya que ambos están en Junio)
        self.assertAlmostEqual(attendance_1.irg_monthly_hours_total, 12.0, places=2)
        self.assertAlmostEqual(attendance_2.irg_monthly_hours_total, 12.0, places=2)

    def test_02_weekly_boundary_conditions(self):
        """Prueba que los límites de semana separen correctamente los totales."""
        
        # Asistencia Semana 1 (Lunes 15 de Junio)
        attendance_w1 = self.env['hr.attendance'].create({
            'employee_id': self.employee_1.id,
            'check_in': datetime(2026, 6, 15, 8, 0, 0),
            'check_out': datetime(2026, 6, 15, 16, 0, 0),
        })
        
        # Asistencia Semana 2 (Lunes 22 de Junio)
        attendance_w2 = self.env['hr.attendance'].create({
            'employee_id': self.employee_1.id,
            'check_in': datetime(2026, 6, 22, 8, 0, 0),
            'check_out': datetime(2026, 6, 22, 14, 0, 0),
        })

        self.env.flush_all()

        # Semanalmente deben estar separadas (8 horas en w1, 6 horas en w2)
        self.assertAlmostEqual(attendance_w1.irg_weekly_hours_total, 8.0, places=2)
        self.assertAlmostEqual(attendance_w2.irg_weekly_hours_total, 6.0, places=2)

        # Mensualmente deben sumarse (8 + 6 = 14 horas porque ambas están en Junio)
        self.assertAlmostEqual(attendance_w1.irg_monthly_hours_total, 14.0, places=2)
        self.assertAlmostEqual(attendance_w2.irg_monthly_hours_total, 14.0, places=2)

    def test_03_monthly_boundary_conditions(self):
        """Prueba que los límites de mes separen correctamente los totales."""
        
        # Asistencia en Junio (Martes 30 de Junio)
        attendance_jun = self.env['hr.attendance'].create({
            'employee_id': self.employee_1.id,
            'check_in': datetime(2026, 6, 30, 8, 0, 0),
            'check_out': datetime(2026, 6, 30, 16, 0, 0),
        })
        
        # Asistencia en Julio (Miércoles 1 de Julio)
        # Nota: el 30 de junio de 2026 es martes, el 1 de julio de 2026 es miércoles.
        # Por lo tanto, están en la misma semana pero en meses distintos.
        attendance_jul = self.env['hr.attendance'].create({
            'employee_id': self.employee_1.id,
            'check_in': datetime(2026, 7, 1, 8, 0, 0),
            'check_out': datetime(2026, 7, 1, 14, 0, 0),
        })

        self.env.flush_all()

        # Semanalmente se suman porque están en la misma semana (8 + 6 = 14 horas)
        self.assertAlmostEqual(attendance_jun.irg_weekly_hours_total, 14.0, places=2)
        self.assertAlmostEqual(attendance_jul.irg_weekly_hours_total, 14.0, places=2)

        # Mensualmente deben estar separadas (8 horas en Junio, 6 horas en Julio)
        self.assertAlmostEqual(attendance_jun.irg_monthly_hours_total, 8.0, places=2)
        self.assertAlmostEqual(attendance_jul.irg_monthly_hours_total, 6.0, places=2)

    def test_04_multiple_employees_isolation(self):
        """Prueba que las horas de diferentes empleados no interfieran entre sí."""
        
        # Asistencia Empleado 1
        attendance_emp1 = self.env['hr.attendance'].create({
            'employee_id': self.employee_1.id,
            'check_in': datetime(2026, 6, 15, 8, 0, 0),
            'check_out': datetime(2026, 6, 15, 16, 0, 0),
        })
        
        # Asistencia Empleado 2 en el mismo día
        attendance_emp2 = self.env['hr.attendance'].create({
            'employee_id': self.employee_2.id,
            'check_in': datetime(2026, 6, 15, 8, 0, 0),
            'check_out': datetime(2026, 6, 15, 13, 0, 0),
        })

        self.env.flush_all()

        # Deben calcularse de forma independiente
        self.assertAlmostEqual(attendance_emp1.irg_weekly_hours_total, 8.0, places=2)
        self.assertAlmostEqual(attendance_emp2.irg_weekly_hours_total, 5.0, places=2)
        
        self.assertAlmostEqual(attendance_emp1.irg_monthly_hours_total, 8.0, places=2)
        self.assertAlmostEqual(attendance_emp2.irg_monthly_hours_total, 5.0, places=2)
