# -*- coding: utf-8 -*-
{
    'name': 'Fix QWeb del tile de certificados',
    'version': '16.0.1.0.0',
    'summary': 'Sustituye hasattr en el tile de certificados del campus por is_diplomado().',
    'category': 'Website',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_campus_certificates_portal',
        'irg_course_portal_tiles_diplomado_hide',
    ],
    'data': [
        'views/campus_dashboard_override.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
