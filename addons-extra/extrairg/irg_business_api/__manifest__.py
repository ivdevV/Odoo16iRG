# -*- coding: utf-8 -*-
{
    'name': 'IRG Business API',
    'version': '16.0.1.1.0',
    'category': 'Education',
    'summary': 'Fachada de comandos académicos cerrados, auditables e idempotentes',
    'description': """
        Modelo de operaciones irg.api.operation para lecturas académicas y
        escrituras eLearning en borrador. No expone el ORM ni métodos arbitrarios.
    """,
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_course_convocatorias_v2',
        'irg_online_subject_opening',
        'openeducat_admission',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/api_operation_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
