# -*- coding: utf-8 -*-
{
    'name': 'iRG Partner OpenEduCat Info',
    'version': '16.0.1.0.0',
    'summary': """Muestra la información educativa de OpenEduCat y la pestaña accesos directamente en los contactos (res.partner).""",
    'author': 'iRG',
    'website': 'https://www.isep.es',
    'category': 'OpenEducat',
    'depends': [
        'base',
        'openeducat_core',
        'isep_student_filter',
        'isep_student_access',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
