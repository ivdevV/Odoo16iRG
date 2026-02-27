{
    'name': 'IRG Timetable Portal Modern UI',
    'version': '16.0.1.0.0',
    'summary': 'Moderniza el diseño del calendario en portal estudiante',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_timetable_enterprise',
    ],
    'data': [
        'views/timetable_portal_overhaul.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_timetable_portal_modern_ui/static/src/scss/portal_timetable_modern.scss',
        ],
    },
    'installable': True,
    'application': False,
}
