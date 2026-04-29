# -*- coding: utf-8 -*-
{
    'name': 'IRG Website Slides Render Fix',
    'version': '16.0.1.0.0',
    'summary': 'Fix fullscreen eLearning slide rendering with custom async overrides',
    'author': 'iRG',
    'category': 'Website/eLearning',
    'license': 'LGPL-3',
    'depends': [
        'website_slides',
        'website_slides_survey',
        'isep_survey',
        'isep_content_interactive_survey',
        'isep_external_video',
        'isep_bunny_elearning',
        'isep_scorm_elearning',
        'isep_slide_article_custom',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_website_slides_render_fix/static/src/js/slides_course_fullscreen_render_fix.js',
        ],
    },
    'installable': True,
    'application': False,
}