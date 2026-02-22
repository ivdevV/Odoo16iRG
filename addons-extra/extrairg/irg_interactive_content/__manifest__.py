# -*- coding: utf-8 -*-
{
    'name': 'IRG Interactive Content',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Render AI-generated interactive learning content on eLearning slides',
    'description': """
        Extiende slide.slide para soportar contenido interactivo generado por IA
        (diagramas Mermaid, flashcards, contenido HTML y quiz de opción múltiple).
    """,
    'author': 'iRG',
    'website': '',
    'depends': [
        'website_slides',
        'website',
        'web',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/slide_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_interactive_content/static/src/js/interactive_loader.js',
            'irg_interactive_content/static/src/css/interactive_content.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
