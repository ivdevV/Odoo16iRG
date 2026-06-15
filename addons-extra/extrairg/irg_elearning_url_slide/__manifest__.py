# -*- coding: utf-8 -*-
{
    'name': 'IRG eLearning URL Slide',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Add URL content type to eLearning slides',
    'description': """
        Adds a URL content type to website_slides so courses can include
        normal slides that link to classes or external learning resources.
    """,
    'author': 'iRG',
    'website': '',
    'depends': [
        'website_slides',
        'website',
        'web',
    ],
    'data': [
        'views/slide_slide_views.xml',
        'views/website_slides_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_elearning_url_slide/static/src/xml/website_slides_fullscreen_url.xml',
            'irg_elearning_url_slide/static/src/js/slides_course_fullscreen_url.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
