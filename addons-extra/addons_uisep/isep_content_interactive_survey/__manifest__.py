# -*- coding: utf-8 -*-
{
    'name': 'Isep Content Interactive Survey',
    'version': '1.1',
    'summary': """ Contenido interactivo de encuestas de tipo asignación """,
    'description': """ Contenido interactivo de encuestas de tipo asignación """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['website_slides','survey', 'isep_survey'],
    "data": [
        "views/survey_survey_views.xml",
        # "views/website_slides_templates.xml",
        # "views/survey_xpath.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'isep_content_interactive_survey/static/src/js/slides_course_fullscreen_player.js',
            'isep_content_interactive_survey/static/src/xml/website_slides_fullscreen.xml',
        ],
    },
    
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
