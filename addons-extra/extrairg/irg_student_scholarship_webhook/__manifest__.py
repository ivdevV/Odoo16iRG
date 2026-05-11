# -*- coding: utf-8 -*-

{
    'name': 'IRG Student Scholarship Webhook',
    'version': '16.0.1.2.0',
    'category': 'OpenEduCat',
    'summary': 'Webhook externo para documentacion de becas de alumnos',
    'description': """
        Adds a secured JSON webhook that lets external applications submit
        scholarship application documents for students and contacts by email.
    """,
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'openeducat_core',
        'irg_student_scholarship_documents',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
