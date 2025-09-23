# -*- coding: utf-8 -*-
{
    'name': 'Contenido Interactivo',
    'version': '16.5',
    'summary': """ Módulo que agrega contenido interáctivo """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['website_slides', 'website_slides_customizations'],
    "data": [
        "views/slide_slide_views.xml",
        "views/website_slides_templates_lesson_inh.xml"
    ],

    'assets': {
        'web.assets_frontend': [
            'isep_content_interactive/static/src/js/slides_course_player.js',
            'isep_content_interactive/static/src/js/slides_course_player_fullscreen.js',
            'isep_content_interactive/static/src/js/download_iframe_pdf.js',
        ],

    },
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
