# -*- coding: utf-8 -*-
{
    'name': 'IRG Admission — Auto Gradebook',
    'version': '16.0.1.0.0',
    'summary': (
        'Crea la libreta de calificaciones automáticamente al confirmar '
        'la matrícula de un alumno (Enroll Student).'
    ),
    'description': """
        Al pulsar "Enroll Student" en una admisión (estado → done), este módulo:

        1. Comprueba si el curso tiene activada la creación automática de libreta.
        2. Verifica que no exista ya una libreta para esa admisión (idempotente).
        3. Crea un registro `app.gradebook.student` vinculado a la admisión.
        4. Puebla automáticamente las asignaturas según el filtro configurado
           en el curso (solo obligatorias o todas).
    """,
    'category': 'Education',
    'author': 'IRG',
    'website': '',
    'depends': [
        'openeducat_admission',
        'isep_gradebook',
        'irg_gradebook_exam_as_final',
    ],
    'data': [
        'views/op_course_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
