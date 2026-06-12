# -*- coding: utf-8 -*-
{
    'name': 'IRG - Ocultar botón Certifies / Diplomas',
    'summary': 'Oculta el botón legacy "Certifies / Diplomas" de la ficha del '
               'estudiante; el flujo vigente es "Generar Diploma" '
               '(irg_generacion_diplomas).',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['isep_openeducat_reports'],
    'data': [
        'views/op_student_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
