# -*- coding: utf-8 -*-
{
    'name': 'iRG n8n Chat Bubble',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Burbuja de chat inteligente de n8n por curso académico en el campus virtual',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'website_slides',
        'openeducat_core',
        'irg_course_convocatorias_v2',
    ],
    'data': [
        'views/op_course_views.xml',
        'views/website_slides_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_n8n_chat_bubble/static/src/js/n8n_chat_bubble.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
