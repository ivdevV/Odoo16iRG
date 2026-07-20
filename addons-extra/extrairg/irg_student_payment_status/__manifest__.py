# -*- coding: utf-8 -*-
{
    'name': 'IRG Student Payment Status',
    'version': '16.0.1.0.0',
    'summary': 'Controla el estado de pago de los alumnos.',
    'category': 'Education',
    'author': 'iRG',
    'depends': [
        'openeducat_core',
        'irg_student_invoice_payment_link',
    ],
    'data': [
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        'views/op_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
