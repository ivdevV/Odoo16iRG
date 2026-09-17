# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Slide Restrictions',
    'version': '16.0.1.1.0',
    'category': 'Website/eLearning',
    'summary': 'Restringe secciones de elearning por modalidad de prácticas',
    'description': """
Añade un requisito de modalidad de prácticas en slides/secciones.
Vacío = visible para todos. Con valor = solo si la matrícula coincide.
    """,
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_student_course_practice_modality',
        'irg_elearning_editable_sections',
        'isep_elearning_custom',
        'irg_batch_slide_restrictions',
    ],
    'data': [
        'views/slide_slide_view.xml',
        'views/slide_channel_view.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
}
