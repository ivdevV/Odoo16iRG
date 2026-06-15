# -*- coding: utf-8 -*-
{
    'name': 'Generación de Diplomados iRG',
    'version': '16.0.1.0.1',
    'summary': 'Módulo independiente para la generación y registro de diplomados iRG.',
    'description': """
        Módulo para la generación y registro de diplomados iRG.
        Permite configurar las asignaturas a imprimir en los diplomados,
        clasificándolas según modalidad presencial u online, e imprimiendo
        el reporte QWeb de dos páginas correspondiente.
    """,
    'author': 'Instituto Raimon Gaja',
    'website': 'https://www.institutografologia.com',
    'category': 'Education',
    'depends': [
        'openeducat_core',
        'web',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/op_subject_views.xml',
        'views/op_course_views.xml',
        'views/op_student_views.xml',
        'views/diplomado_registry_views.xml',
        'wizard/diplomado_wizard_views.xml',
        'reports/diplomado_report.xml',
        'reports/diplomado_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
