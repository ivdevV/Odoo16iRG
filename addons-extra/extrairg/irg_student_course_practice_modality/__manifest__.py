# -*- coding: utf-8 -*-
{
    'name': 'IRG Student Course Practice Modality',
    'version': '16.0.1.1.0',
    'category': 'Education',
    'summary': 'Modalidad de prácticas por matrícula del estudiante',
    'description': """
Guarda la modalidad de prácticas en op.student.course, la sincroniza desde
la solicitud de prácticas y la muestra en backend y campus.
    """,
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
        'isep_practices_2',
        'irg_practice_center_type_modalities',
        'isep_website_custom',
        'openeducat_core_enterprise',
        'isep_student_filter',
    ],
    'data': [
        'views/op_student_course_views.xml',
        'views/op_student_views.xml',
        'views/user_profile_templates.xml',
        'views/educational_info_portal.xml',
    ],
    'installable': True,
    'application': False,
}
