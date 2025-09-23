# -*- coding: utf-8 -*-
{
    'name': 'Isep - Documentos Endpoint',
    'version': '16.1',
    'summary': """ Módulo para la gestión de documentos endpoint """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['isep_record_request', ],
    "data": [
        "views/res_config_settings_views.xml"
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
