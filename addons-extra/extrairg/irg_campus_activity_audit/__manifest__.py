# -*- coding: utf-8 -*-
{
    "name": "iRG Campus Activity Audit",
    "version": "16.0.1.1.0",
    "category": "Education",
    "summary": "Informe Excel de actividad de campus a partir del listado de alumnos",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": [
        "openeducat_core",
        "isep_elearning_custom",
        "isep_student_filter",
        "isep_gradebook",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/campus_activity_audit_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
