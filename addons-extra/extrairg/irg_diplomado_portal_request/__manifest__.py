# -*- coding: utf-8 -*-
{
    'name': 'Portal de Solicitudes de Diplomas de Diplomados',
    'version': '16.0.1.0.0',
    'summary': 'Solicitudes portal de diplomas de diplomados con validacion de nota final superior a 7.',
    'category': 'Website',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'portal',
        'mail',
        'irg_course_portal_tiles',
        'irg_campus_certificates_portal',
        'irg_generacion_diplomados',
        'isep_gradebook',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/diplomado_portal_request_views.xml',
        'views/course_portal_tiles.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
