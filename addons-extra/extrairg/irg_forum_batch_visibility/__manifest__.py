# -*- coding: utf-8 -*-
{
    'name': 'IRG - Forum Batch Visibility',
    'version': '16.0.3.0.0',
    'category': 'Website/Forum',
    'summary': 'Limit forum visibility by custom batches',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'website_forum',
        'openeducat_core',
    ],
    'data': [
        'security/forum_batch_visibility_rules.xml',
        'views/forum_batch_visibility_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_forum_batch_visibility/static/src/js/forum_publish_feedback.js',
            'irg_forum_batch_visibility/static/src/scss/forum_editor_focus.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
}
