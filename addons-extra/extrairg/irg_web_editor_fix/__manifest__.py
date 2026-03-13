# -*- coding: utf-8 -*-
{
    'name': 'IRG Web Editor Fix',
    'version': '16.0.1.0',
    'category': 'Tools',
    'summary': 'Fix TypeError in OdooEditor _applyRawCommand method',
    'description': 'Este modulo parchea el metodo _applyRawCommand de OdooEditor para prevenir el error TypeError que ocurre al editar contenido en el editor WYSIWYG',
    'author': 'Instituto Raimon Gaja',
    'website': 'https://www.institutoraimongaja.com',
    'depends': [
        'web_editor',
    ],
    'data': [
        'views/assets.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}
