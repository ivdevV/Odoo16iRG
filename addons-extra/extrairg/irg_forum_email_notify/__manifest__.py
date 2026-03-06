# -*- coding: utf-8 -*-
{
    'name': 'IRG - Forum Email Notifications',
    'version': '16.0.1.0.0',
    'category': 'Website/Forum',
    'summary': 'Send email notifications to forum participants on new posts',
    'description': """
        Sends an email to all eligible forum participants whenever a new post
        (question or reply) is published.  Recipients are determined by the
        forum's visibility configuration (batch / course).  Each email
        includes the full post content, a link to the thread, and a
        one-click unsubscribe link.
    """,
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'website_forum',
        'website',
        'openeducat_core',
        'irg_forum_batch_visibility',
    ],
    'data': [
        'data/mail_template.xml',
        'views/forum_forum_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
