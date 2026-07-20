{
    'name': 'IRG - Forum Notice Global Seen',
    'version': '16.0.1.0.0',
    'category': 'Website/Forum',
    'summary': 'Show each forum notice once per user',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['irg_forum_notice_popup'],
    'data': [
        'security/forum_notice_seen_rules.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            (
                'remove',
                'irg_forum_notice_popup/static/src/js/forum_notice_popup.js',
            ),
            'irg_forum_notice_global_seen/static/src/js/forum_notice_popup.js',
        ],
    },
    'installable': True,
    'application': False,
}
