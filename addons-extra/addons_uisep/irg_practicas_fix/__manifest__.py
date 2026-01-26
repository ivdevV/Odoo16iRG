# -*- coding: utf-8 -*-
{
    'name': 'IRG Prácticas Fix',
    'version': '16.0.1.0.0',
    'summary': 'Correcciones y mejoras para el módulo de prácticas',
    'description': """
        Este módulo contiene correcciones para el módulo isep_practices_2:
        - Corrige el campo user_id para que sea relacionado con op_student_id.user_id
        - Mejora la vista del formulario con un flujo más lógico
    """,
    'author': 'IRG',
    'category': 'Education',
    'depends': [
        'isep_practices_2',
    ],
    'data': [
        'views/practice_request_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
