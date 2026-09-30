# -*- coding: utf-8 -*-
{
    'name': 'IRG - Forum Web Post Batches',
    'version': '16.0.1.0.0',
    'category': 'Website/Forum',
    'summary': 'Choose visible batches when an internal user creates a forum post on the website',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'website_forum',
        'irg_forum_batch_visibility',
        'openeducat_core',
        'openeducat_admission',
    ],
    'data': [
        'views/new_question.xml',
    ],
    'installable': True,
    'auto_install': False,
}
