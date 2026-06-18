# -*- coding: utf-8 -*-
{
    'name': 'IRG Diploma Gradebook Weighting',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Aplica ponderación 50/50 y recuperación general para diplomados.',
    'description': """
        Extiende las libretas de isep_gradebook para cursos tipo Diplomado:
        50% Módulo Presencial y 50% promedio del resto de módulos obligatorios.
        Cuando el resultado base es menor a 7, permite registrar una recuperación
        general del diplomado con nota máxima 7.
    """,
    'author': 'IRG',
    'depends': [
        'isep_gradebook',
        'isep_control_escolar',
        'isep_student_migration',
    ],
    'data': [
        'views/app_gradebook_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
