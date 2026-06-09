# -*- coding: utf-8 -*-
{
    'name': 'IRG Academic Request History',
    'version': '16.0.1.0.0',
    'summary': 'Historial y trazabilidad de solicitudes academicas de portal.',
    'category': 'Education',
    'author': 'iRG',
    'depends': [
        'irg_gradebook_certificates',
        'irg_generacion_diplomas',
        'openeducat_core',
    ],
    'data': [
        'views/irg_certificate_request_views.xml',
        'views/res_partner_views.xml',
        'views/op_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
