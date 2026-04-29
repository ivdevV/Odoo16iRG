# -*- coding: utf-8 -*-
{
    'name': 'IRG Content Interactive Super Fix',
    'version': '16.0.1.0.0',
    'summary': 'Fix async _super usage in fullscreen interactive content',
    'author': 'iRG',
    'category': 'Website/eLearning',
    'license': 'LGPL-3',
    'depends': [
        'isep_content_interactive',
    ],
    'assets': {
        'web.assets_frontend': [
            (
                'replace',
                'isep_content_interactive/static/src/js/slides_course_player_fullscreen.js',
                'irg_content_interactive_super_fix/static/src/js/slides_course_player_fullscreen.js',
            ),
        ],
    },
    'installable': True,
    'application': False,
}