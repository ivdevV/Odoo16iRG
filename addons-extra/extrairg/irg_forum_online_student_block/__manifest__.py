# -*- coding: utf-8 -*-
{
    'name': 'IRG - Forum Online Student Block',
    'version': '16.0.1.0.0',
    'category': 'Website/Forum',
    'summary': 'Block online students from campus course forums',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'website_forum',
        'website',
        'openeducat_core',
        'irg_forum_batch_visibility',
        'irg_campus_course_forum',
        'irg_forum_email_notify',
        'irg_forum_followers_post_notify',
    ],
    'data': [
        'security/forum_online_student_rules.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}