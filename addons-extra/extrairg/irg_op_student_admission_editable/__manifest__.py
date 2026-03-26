# -*- coding: utf-8 -*-
{
    'name': 'IRG Op Student Admission Editable',
    'version': '16.0.1.0.0',
    'category': 'OpenEduCat',
    'summary': 'Makes the admission popup in the student form editable and shows grade averages',
    'description': """
        Adds a gradebook subjects One2many field to op.admission and overrides the
        inline admission form in the op.student view to:
        - Allow editing of key admission fields (date, course, batch, due date, state)
        - Display the associated gradebook subjects with grade averages (read-only)
    """,
    'author': 'IRG',
    'depends': [
        'openeducat_core',
        'openeducat_admission',
        'isep_student_filter',
        'isep_gradebook',
    ],
    'data': [
        'views/op_student_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
