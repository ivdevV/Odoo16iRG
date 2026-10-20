# -*- coding: utf-8 -*-
{
    'name': 'IRG Invoice Dotacion Banner',
    'version': '16.0.1.0.0',
    'summary': 'Cinta de dotación por morosidad en la factura de cliente.',
    'category': 'Accounting',
    'author': 'iRG',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'irg_invoice_dotacion_banner/static/src/scss/dotacion_ribbon.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
