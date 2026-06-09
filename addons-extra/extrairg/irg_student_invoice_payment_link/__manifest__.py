# -*- coding: utf-8 -*-
{
    'name': 'IRG Student Invoice Payment Link',
    'version': '16.0.1.0.0',
    'summary': 'Vincula facturas y pagos de terceros con la ficha academica del alumno.',
    'category': 'Education',
    'author': 'iRG',
    'depends': [
        'account',
        'sale',
        'openeducat_fees',
        'irg_sale_order_extended',
    ],
    'data': [
        'views/account_move_views.xml',
        'views/op_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
