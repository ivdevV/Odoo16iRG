# -*- coding: utf-8 -*-
{
    "name": "iRG Attendance Hours",
    "summary": "Total de horas semanales y mensuales en asistencias",
    "description": """
        Calcula y muestra el total de horas semanales y mensuales trabajadas de un empleado
        en cada registro de asistencia del modelo hr.attendance.
    """,
    "version": "16.0.1.0.0",
    "category": "Human Resources/Attendances",
    "author": "iRG",
    "license": "AGPL-3",
    "depends": [
        "hr_attendance",
    ],
    "data": [
        "views/hr_attendance_views.xml",
    ],
    "installable": True,
    "application": False,
}
