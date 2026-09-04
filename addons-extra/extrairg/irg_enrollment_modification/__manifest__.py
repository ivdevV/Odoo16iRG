# -*- coding: utf-8 -*-
{
    'name': 'IRG Modificación de matrícula',
    'summary': 'Solicitud y vistos de cambio de curso, lote, modalidad, año y forma de pago',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'author': 'Instituto Raimon Gaja',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
        'mail',
        'sale',
        'account_payment_sale',
    ],
    'external_dependencies': {
        'python': ['docx'],
    },
    'data': [
        'security/enrollment_change_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/enrollment_change_wizard_views.xml',
        'views/enrollment_change_views.xml',
        'views/op_student_views.xml',
    ],
    'installable': True,
    'application': False,
}
