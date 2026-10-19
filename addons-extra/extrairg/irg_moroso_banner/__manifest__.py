# -*- coding: utf-8 -*-
{
    'name': 'IRG Moroso Banner',
    'version': '16.0.1.1.0',
    'summary': 'Cinta de moroso en el contacto y en el alumno.',
    'category': 'Education',
    'author': 'iRG',
    'depends': [
        'account',
        'openeducat_core',
        'irg_student_invoice_payment_link',
        'irg_invoice_dotacion_banner',
    ],
    'data': [
        'data/ir_cron.xml',
        'views/res_partner_views.xml',
        'views/op_student_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'irg_moroso_banner/static/src/scss/moroso_ribbon.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
