# -*- coding: utf-8 -*-
{
    'name': 'IRG Admission — Auto Gradebook Templates',
    'version': '16.0.1.2.0',
    'summary': (
        'Asigna plantilla de calificaciones al crear/actualizar una libreta '
        'con admisión (curso, o canónicas máster/diplomado).'
    ),
    'description': """
        Al crear una libreta (app.gradebook.student) con admisión, o al
        matricular con irg_admission_auto_gradebook:

        1. Si el curso tiene gradebook_id, se conserva.
        2. Si no, diplomado → plantilla Diplomado 50/50.
        3. Si no, máster → Solo Examen (xml_id o nombre).
        4. Resto: libreta sin plantilla.
    """,
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_admission_auto_gradebook',
        'irg_gradebook_editable_template',
        'irg_gradebook_partial_averages',
        'irg_diploma_gradebook_template_weighting',
        'irg_diploma_gradebook_beta_course_detection',
    ],
    'data': [
        'data/gradebook_template_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
