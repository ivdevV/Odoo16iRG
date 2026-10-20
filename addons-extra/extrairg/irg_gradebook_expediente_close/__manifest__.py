# -*- coding: utf-8 -*-
{
    "name": "IRG Cierre de expediente al autocerrar la libreta",
    "version": "16.0.1.0.0",
    "summary": "Registra la fecha de cierre de expediente y avisa a académica",
    "author": "iRG",
    "category": "Education",
    "depends": [
        "irg_gradebook_auto_close",
        "isep_gradebook",
        "isep_student_filter",
        "mail",
    ],
    "data": [
        "data/mail_template.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
