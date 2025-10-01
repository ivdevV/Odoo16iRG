# -*- coding: utf-8 -*-
{
    'name': "isep_restrict_portal_modules",
    'summary': "Adds portal module restriction",
    'description': "Adds portal module restriction",
    'author': "Gianmarco Contreras",
    'website': "https://github.com/CodigoByte2020",
    'category': 'website',
    'version': '1.0',
    'depends': [
        'openeducat_web',
        'isep_website_custom',
        'isep_student_filter'
    ],
    'data': [
        'views/openeducat_portal_menu.xml',
        'views/user_profile_openeducat.xml'
    ]
}
