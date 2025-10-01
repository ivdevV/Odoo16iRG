# -*- coding: utf-8 -*-
{
    'name': 'Update Password User',
    'version': '16.2',
    'summary': """ Actualizar contraseña del usuario - flujo ecommerce/admision """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['base', 'auth_signup', 'isep_elearning_custom'],
    "data": [
        "data/op_admission_welcome.xml",
        "views/res_users_views.xml"
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
