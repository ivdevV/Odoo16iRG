# -*- coding: utf-8 -*-
{
    "name": "iRG Campus Activity Audit",
    "version": "16.0.1.0.0",
    "category": "Education",
    "summary": "Informe Excel de actividad de campus desde el lote interno",
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
        "views/op_batch_views.xml",
    ],
    "installable": True,
    "application": False,
}
