# -*- coding: utf-8 -*-
{
    "name": "iRG Student Activity",
    "version": "16.0.1.0.0",
    "category": "Education",
    "summary": "Historial de actividad de campus y evaluaciones en la ficha del alumno",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": [
        "openeducat_core",
        "isep_student_access",
        "isep_elearning_custom",
        "website_slides_survey",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/op_student_views.xml",
        "wizard/activity_export_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
