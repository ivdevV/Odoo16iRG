{
    'name': 'IRG Google Calendar Sync',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Sync Google Calendar Events to OpenEduCat Sessions',
    'author': 'Copilot',
    'depends': ['calendar', 'openeducat_timetable', 'openeducat_core'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/calendar_event_view.xml',
    ],
    'installable': True,
    'application': False,
}
