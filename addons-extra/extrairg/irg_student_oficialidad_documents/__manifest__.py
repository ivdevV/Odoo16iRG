# -*- coding: utf-8 -*-
{
    'name': 'IRG Student Oficialidad Documents',
    'version': '16.0.1.0.0',
    'category': 'OpenEduCat',
    'summary': 'Documentos de oficialidad del alumno (catalogo de tipos)',
    'description': """
        Catalogo de tipos de documentos de oficialidad requeridos al alumno
        nacional o internacional.
    """,
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'openeducat_core',
        'isep_control_escolar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/oficialidad_document_type_data.xml',
        'views/op_student_views.xml',
        'views/oficialidad_document_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
