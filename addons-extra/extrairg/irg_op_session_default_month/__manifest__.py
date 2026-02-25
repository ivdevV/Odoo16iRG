# -*- coding: utf-8 -*-
{
    'name': 'IRG - OpenEduCat Timetable Default Month',
    'summary': 'Set portal timetable default view to month',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'author': 'iRG',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_timetable_enterprise',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_op_session_default_month/static/src/js/portal_timetable_month_default.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
