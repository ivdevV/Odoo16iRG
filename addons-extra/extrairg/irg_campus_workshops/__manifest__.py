# -*- coding: utf-8 -*-
{
    'name': 'IRG - Talleres en Campus',
    'summary': 'Añade una sección de talleres en el portal /campus con el tile de iRG Empower',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'isep_website_custom',
        'isep_website_custom_design',
    ],
    'data': [
        'views/user_profile_content_workshops.xml',
    ],
    'installable': True,
    'auto_install': False,
}
