# -*- coding: utf-8 -*-
{
    'name': 'IRG Auto Translate',
    'version': '16.0.1.0.0',
    'summary': (
        'Automatic translation of course/subject names via DeepL or Google Translate. '
        'All API calls run synchronously inside ir.cron — no background threads.'
    ),
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'openeducat_core',
        'irg_language_nav',
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    # Queue all existing courses & subjects for translation on first install
    'post_init_hook': 'post_init_hook',
}
