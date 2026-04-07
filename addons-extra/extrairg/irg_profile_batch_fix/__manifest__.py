# -*- coding: utf-8 -*-
{
    'name': 'IRG Profile Batch Fix',
    'version': '16.0.1.0.0',
    'summary': (
        'Corrige nombre incorrecto en tarjetas de programa del campus y '
        'filtra el calendario por batch cuando se accede desde un curso específico.'
    ),
    'category': 'Education',
    'author': 'IRG',
    'depends': [
        'isep_website_custom',
        'isep_website_custom_design',
        'irg_course_portal_tiles',
        'isep_time_link_url',
    ],
    'data': [
        'views/user_profile_content_fix.xml',
        'views/irg_tiles_calendar_fix.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_profile_batch_fix/static/src/js/timetable_batch_filter.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
