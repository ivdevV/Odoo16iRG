# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Preferred Quarter',
    'version': '16.0.1.0.0',
    'summary': 'Trimestre preferente para iniciar las prácticas en solicitud portal y backend',
    'author': 'IRG',
    'category': 'Education',
    'depends': [
        'isep_practices_2',
        'irg_practice_center_restrict',
        'irg_practice_request_student_profile',
    ],
    'data': [
        'views/practice_request_views.xml',
        'views/practice_request_portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
