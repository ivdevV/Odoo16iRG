# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Center Documents',
    'version': '16.0.1.0.1',
    'summary': 'Añade adjuntos documentales a los centros de prácticas',
    'description': """
        Permite subir y gestionar documentos asociados a cada centro de
        prácticas desde la ficha backend de Practice Centers.
    """,
    'author': 'IRG',
    'category': 'Education',
    'depends': [
        'isep_practices_2',
    ],
    'data': [
        'views/practice_center_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
