{
    'name': 'IRG - Forum Notice Popup',
    'version': '16.0.1.0.0',
    'category': 'Website/Forum',
    'summary': 'Show class forum notices as popup filtered by batch',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'website_forum',
        'irg_campus_course_forum',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_forum_notice_popup/static/src/js/forum_notice_popup.js',
            'irg_forum_notice_popup/static/src/js/forum_share_override.js',
            'irg_forum_notice_popup/static/src/scss/forum_notice_popup.scss',
        ],
    },
    'installable': True,
    'application': False,
}
