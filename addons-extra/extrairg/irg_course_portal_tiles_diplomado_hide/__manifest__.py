# -*- coding: utf-8 -*-
{
    'name': 'IRG Course Portal Tiles Diplomado Hide',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Oculta tiles de Prácticas y TFM para alumnos de Diplomados en el portal del curso',
    'depends': [
        'irg_course_portal_tiles',
        'openeducat_core',
        'product',
    ],
    'data': [
        'views/irg_course_portal_tiles_views.xml',
    ],
    'test-enable': True,
    'installable': True,
    'license': 'LGPL-3',
}
