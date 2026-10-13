# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Center CIF',
    'version': '16.0.1.0.0',
    'summary': 'CIF en la ficha de los centros de prácticas',
    'description': """
        Añade el CIF a cada centro de prácticas y lo usa al generar
        el contacto y al prellenar el NIF/CIF de un convenio nuevo.
    """,
    'author': 'IRG',
    'category': 'Education',
    'depends': [
        'isep_practices_2',
        'irg_practice_agreement_sign',
    ],
    'data': [
        'views/practice_center_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
