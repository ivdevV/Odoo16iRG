# -*- coding: utf-8 -*-
{
    'name': 'IRG Gradebook - Borrar Asignaturas',
    'summary': 'Añade un botón en app.gradebook.student para eliminar todas las asignaturas de golpe.',
    'version': '16.0.1.2.0',
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['isep_gradebook'],
    'data': [
        'security/ir.model.access.csv',
        'views/app_gradebook_student_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
