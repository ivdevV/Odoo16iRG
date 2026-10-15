# -*- coding: utf-8 -*-

{
    'name': 'IRG Student Oficialidad Webhook',
    'version': '16.0.1.0.0',
    'category': 'OpenEduCat',
    'summary': 'Webhook externo para documentacion de oficialidad de alumnos',
    'description': """
        Adds a secured JSON webhook that lets the external oficialidad
        application submit Unimarconi documents for students and contacts by
        email. The bearer token lives in the system parameter
        irg_student_oficialidad_webhook.token and must be set per environment.
    """,
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'irg_student_oficialidad_documents',
    ],
    'data': [
        'data/oficialidad_webhook_params.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
