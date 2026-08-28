# -*- coding: utf-8 -*-
{
    'name': 'IRG - Tipo de titulación del estudiante',
    'version': '16.0.1.0.0',
    'summary': 'Etiqueta de tipo de titulación en la ficha de alumno',
    'author': 'iRG',
    'category': 'Education',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/irg_student_degree_type_views.xml',
        'views/op_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
