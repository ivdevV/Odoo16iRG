# -*- coding: utf-8 -*-
{
    'name': 'IRG Website Slides Download Fix',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Fix PDF download in website slides and prevent JS crash for non-standard content.',
    'description': """
        Añade un parche local que corrige el botón de descarga PDF en slides de e-learning.
        Evita errores JavaScript cuando el contenido no tiene la estructura esperada.
    """,
    'author': 'iRG',
    'website': '',
    'depends': [
        'website_slides',
        'website',
        'web',
    ],
    'data': [],
    'assets': {
        'web.assets_frontend': [
            'irg_website_slides_download_fix/static/src/js/slides_download_fix.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
