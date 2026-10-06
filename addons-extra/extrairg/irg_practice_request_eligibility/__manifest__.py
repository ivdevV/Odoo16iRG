# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Request Eligibility',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Solicitud de prácticas desde el 50% de avance, sin diplomados',
    'description': """
El alumno solo puede solicitar prácticas cuando la matrícula alcanza
al menos el 50% de completion_porc y el curso no es un diplomado.
El bloqueo se aplica en el servidor.
    """,
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'isep_practices_2',
        'isep_student_filter',
        'isep_restrict_portal_modules',
        'irg_course_portal_tiles_diplomado_hide',
        'irg_practice_request_online_types',
    ],
    'data': [
        'views/practice_request_eligibility_templates.xml',
    ],
    'installable': True,
    'application': False,
}
