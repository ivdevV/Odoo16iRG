# -*- coding: utf-8 -*-
{
    'name': 'IRG Admission Oficialidad Webhook',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'license': 'LGPL-3',
    'depends': ['openeducat_core', 'openeducat_admission'],
    'data': [
        'security/ir.model.access.csv',
        'data/oficialidad_webhook_params.xml',
        'wizard/oficialidad_send_wizard_view.xml',
        'views/op_admission_register_view.xml',
        'views/op_admission_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
