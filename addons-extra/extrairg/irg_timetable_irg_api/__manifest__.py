{
    'name': 'IRG Timetable — API Calendarios IRG',
    'version': '16.0.1.0.0',
    'summary': 'Calendario portal estudiantil consumiendo API externa de Calendarios IRG',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_timetable_enterprise',
    ],
    'data': [
        'views/portal_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_timetable_irg_api/static/src/js/irg_timetable_api.js',
            'irg_timetable_irg_api/static/src/scss/irg_timetable_api.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
