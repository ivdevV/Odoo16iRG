# -*- coding: utf-8 -*-
{
    'name': 'ISEP Update Pass User Ext',
    'version': '16.1',
    'summary': """ Module to extend user creation with random password """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['base','isep_update_pass_user', ],
    "data": [
        'security/res_groups.xml',
        'views/res_users_views.xml',
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
