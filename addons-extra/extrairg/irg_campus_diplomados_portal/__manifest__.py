# -*- coding: utf-8 -*-
{
    'name': 'Portal de Diplomados',
    'version': '16.0.1.0.0',
    'summary': 'Permite a los alumnos visualizar y descargar sus diplomas de posgrados y diplomados si superan la calificación de 7.0.',
    'category': 'Website',
    'author': 'iRG',
    'depends': [
        'website',
        'portal',
        'irg_campus_certificates_portal',
        'irg_generacion_diplomados',
        'isep_gradebook',
        'irg_course_portal_tiles_diplomado_hide',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
