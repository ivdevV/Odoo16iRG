# -*- coding: utf-8 -*-
{
    'name': "IRG - Sign Reposition",
    'summary': "Reubica y ajusta posiciones de los recuadros de firma en la matrícula",
    'description': """
        Este módulo proporciona una lógica alternativa para crear plantillas de firma
        (`sign.template` / `sign.item`) con posiciones ajustadas (posY/posX) para
        alinear correctamente la casilla de firma en la matrícula.
    """,
    'author': "IRG",
    'category': 'Sale',
    'version': '16.0.1.0.0',
    'depends': [
        'isep_sign_sale',
        'irg_sale_order_extended',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
}
