# -*- coding: utf-8 -*-
{
    'name': "IRG - Sign Position Fix",
    'summary': "Ajusta la posición del recuadro de firma en el documento de matrícula",
    'description': """
        Corrige la posición vertical (posY) del campo de firma en el documento
        de matrícula para que quede a la misma altura que la firma de IRG.
    """,
    'author': "IRG",
    'category': 'Sale',
    'version': '16.0.1.0.0',
    'depends': [
        'isep_sign_sale',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
}
