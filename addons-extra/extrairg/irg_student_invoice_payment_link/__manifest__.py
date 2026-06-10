# -*- coding: utf-8 -*-
{
    'name': 'IRG Student Invoice Payment Link',
    'version': '16.0.1.1.0',
    'summary': 'Vincula facturas y pagos de terceros con la ficha academica del alumno.',
    'description': """
Vincula facturas y pagos reconciliados con la ficha academica del alumno
cuando el titular contable de la factura es un tercero.
""",
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
    'post_init_hook': 'post_init_hook',
}
