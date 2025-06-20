{
    'name': "Odoo Moodle Connector",
    'summary': """
        Moodle Connector with ODOO having Categories, Courses, Users & Events including customize CronJob Configuration.""",
    'description': """
        Synchronization of ODOO with Moodle.
        Once data created in Moodle account, will be reflected in ODOO by just one click.
        It will help out the synchronize Moodle data using customize CronJob settings.
    """,
    'author': "WoadSoft",
    'website': "https://woadsoft.com/",
    'category': 'Website',
    'version': '1.0',
    'depends': ['base', 'contacts', 'calendar', 'website_slides', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/slide_channel_views.xml',
        'views/res_partner_views.xml',
        'views/calendar_event_views.xml',
        'views/moodle_categories_views.xml',
        'views/credentials_views.xml',
        'views/connector_views.xml',
        'views/import_stats_views.xml',
        'views/export_stats_views.xml',
        'views/cronjob_settings_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'price': 200,
    'currency': 'EUR',
    'license': 'OPL-1',
    'images': ["images/banner.gif"],
    'application': True
}
