# -*- coding: utf-8 -*-
{
    'name': 'IRG Timetable Subject Prefix',
    'version': '16.0.1.0.0',
    'summary': 'Muestra código de asignatura en el título del timetable portal',
    'author': 'iRG',
    'website': '',
    'category': 'Education',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_timetable_enterprise',
        'isep_openeducat_custom',
        'isep_time_link_url',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
