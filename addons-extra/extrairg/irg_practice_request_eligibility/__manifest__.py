# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Request Eligibility',
    'version': '16.0.1.3.0',
    'category': 'Education',
    'summary': 'Solicitud de prácticas desde el 60% de avance, sin diplomados',
    'description': """
El alumno solo puede solicitar prácticas cuando la matrícula alcanza
al menos el 60% de completion_porc y el curso no es un diplomado.
En Neuropsicología Clínica (NC/MNC) la parte 1 se abre al 25% y la
parte 2 sigue en el 60%.
Dentro del máster, el cuadro de prácticas permanece visible y explica
el bloqueo hasta que se cumple ese avance.
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
