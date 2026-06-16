# -*- coding: utf-8 -*-
{
    'name': 'Verificacion Web de Diplomas de Diplomados',
    'version': '16.0.1.0.0',
    'summary': 'Valida diplomas de diplomados desde el QR en el sitio web Odoo.',
    'category': 'Website',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'irg_generacion_diplomas',
        'irg_generacion_diplomados',
    ],
    'data': [
        'views/diplomado_verify_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
