# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Request Student Profile',
    'version': '16.0.1.0.0',
    'summary': 'Perfil del alumno en solicitudes de práctica',
    'author': 'IRG',
    'category': 'Education',
    'depends': ['irg_practice_center_restrict'],
    'data': [
        'security/ir.model.access.csv',
        'views/practice_request_views.xml',
        'views/practice_request_portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
