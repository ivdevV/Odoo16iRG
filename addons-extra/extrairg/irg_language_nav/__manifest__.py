# -*- coding: utf-8 -*-
{
    'name': 'IRG Language Nav',
    'version': '16.0.1.0.0',
    'summary': 'Language selector in website top bar (ES/EN first, then alphabetical)',
    'category': 'Website',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'views/language_nav.xml',
    ],
    'installable': True,
    'auto_install': False,
    # NOTE: theme_silon/header.xml already calls irg_language_nav.irg_language_selector
    # so this module must be installed whenever theme_silon is active.
}
