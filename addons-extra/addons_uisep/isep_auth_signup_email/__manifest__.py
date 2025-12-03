# -*- coding: utf-8 -*-
{
    'name': 'ISEP Auth Signup Email Custom',
    'version': '16.0.1.0.0',
    'summary': """ Customization of the Auth Signup Welcome Email """,
    'author': 'ISEP',
    'website': '',
    'category': 'Authentication',
    'depends': ['base', 'auth_signup'],
    "data": [
        "data/auth_signup_data.xml",
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
