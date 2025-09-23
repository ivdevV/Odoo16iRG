# -*- coding: utf-8 -*-
{
    'name': 'Isep Website Custom Design',
    'version': '16.2',
    'summary': """ Isep Website Custom Design """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['isep_website_custom', 'website_profile', 'isep_openeducat_custom'],
    "data": [
        "security/ir.model.access.csv",
        "views/course_admission_icon_views.xml",
        "views/user_profile_content.xml",
        "views/user_profile_content_details.xml",
        "views/user_profile_openeducat.xml",
        "views/website_profile.xml"
    ],

    'assets': {
        'web.assets_frontend': [
            '/isep_website_custom_design/static/src/scss/style.scss',
        ],
    },
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
