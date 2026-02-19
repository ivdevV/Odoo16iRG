# -*- coding: utf-8 -*-
{
    'name': 'IRG - Campus Course Forum',
    'version': '16.0.1.0.0',
    'category': 'Website/Forum',
    'summary': 'Show course forum section in campus course panel',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'isep_website_custom',
        'openeducat_lms_forum',
        'irg_forum_batch_visibility',
    ],
    'data': [
        'views/user_profile_course_forum.xml',
    ],
    'installable': True,
    'auto_install': False,
}
