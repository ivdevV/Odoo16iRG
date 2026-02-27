{
    'name': 'IRG Timetable Portal Overhaul V2',
    'version': '16.0.1.0.0',
    'summary': 'Overhaul estructural del calendario portal estudiantil',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_timetable_enterprise',
    ],
    'data': [
        'views/timetable_portal_overhaul_v2.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_timetable_portal_overhaul_v2/static/src/js/portal_timetable_overhaul_v2.js',
            'irg_timetable_portal_overhaul_v2/static/src/scss/portal_timetable_overhaul_v2.scss',
        ],
    },
    'installable': True,
    'application': False,
}
