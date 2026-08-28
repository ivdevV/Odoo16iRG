# -*- coding: utf-8 -*-
{
    'name': 'IRG eLearning Moodle Category Optional',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Allow eLearning courses without a Moodle category',
    'author': 'iRG',
    'website': '',
    'depends': [
        'odoo_moodle_connector',
    ],
    'data': [
        'views/slide_channel_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
