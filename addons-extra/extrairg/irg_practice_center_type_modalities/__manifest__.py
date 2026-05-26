# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Center Type Modalities',
    'version': '16.0.1.0.0',
    'summary': 'Ajusta las modalidades de tipos de centro de practicas',
    'description': """
        Actualiza las modalidades disponibles en Practice Center Types con
        las denominaciones academicas requeridas por IRG.
    """,
    'author': 'IRG',
    'category': 'Education',
    'depends': [
        'isep_practices_2',
    ],
    'data': [
        'data/practice_center_type_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
