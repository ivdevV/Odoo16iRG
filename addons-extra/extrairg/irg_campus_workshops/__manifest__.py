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
        'irg_course_portal_tiles_diplomado_hide',
    ],
    'data': [
        'views/user_profile_content_workshops.xml',
    ],
    'installable': True,
    'auto_install': False,
}
