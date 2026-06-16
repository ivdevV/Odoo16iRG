# -*- coding: utf-8 -*-
{
    'name': 'Duracion y ECTS en Cursos para Diplomados',
    'version': '16.0.1.0.0',
    'summary': 'Anade horas y ECTS al curso para diplomas de diplomados.',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_generacion_diplomados',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/op_course_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
