# -*- coding: utf-8 -*-
{
    'name': 'IRG eLearning Styles Rework',
    'version': '16.0.1.0.0',
    'summary': 'Rework visual moderno para páginas de eLearning',
    'category': 'Website/eLearning',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'website_slides',
        'website',
        'openeducat_lms',
        'openeducat_lms_website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/website_slides_rework.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_elearning_styles_rework/static/src/scss/irg_elearning_styles_rework.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
