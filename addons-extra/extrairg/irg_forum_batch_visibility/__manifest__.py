# -*- coding: utf-8 -*-
{
    'name': 'IRG - Forum Batch Visibility',
    'version': '16.0.1.0.0',
    'category': 'Website/Forum',
    'summary': 'Limit forum visibility by custom batches',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'website_forum',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/forum_batch_visibility_rules.xml',
        'views/forum_batch_visibility_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
