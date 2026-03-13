# -*- coding: utf-8 -*-
{
    'name': 'IRG Web Editor Fix',
    'version': '16.0.1.0',
    'category': 'Tools',
    'summary': 'Fix TypeError in OdooEditor _applyRawCommand method',
    'description': """
        IRG Web Editor Fix
        ===================
        Este módulo parchea el método _applyRawCommand de OdooEditor
        para prevenir el error "sel.anchorNode[method] is not a function"
        que ocurre al editar contenido en el editor WYSIWYG.
    """,
    'author': 'Instituto Raimon Gaja',
    'website': 'https://www.institutoraimongaja.com',
    'depends': [
        'web_editor',
    ],
    'data': [
        'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': [],
        'web.assets_frontend': [],
        'web_editor.assets_wysiwyg': [],
    },
    'demo': [],
    'installable': True,
    'application': False,
}
