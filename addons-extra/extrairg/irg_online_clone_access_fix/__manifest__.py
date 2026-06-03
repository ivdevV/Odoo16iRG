{
    'name': 'IRG Online Clone Access Fix',
    'version': '16.0.1.0.0',
    'summary': 'Usa el canal Online clonado para accesos y sincronizacion de asignaturas online',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_course_convocatorias_v2',
        'irg_online_subject_opening',
        'irg_online_subject_portal_visibility',
        'irg_subject_fix',
        'website_slides',
    ],
    'data': [
        'views/slide_channel_views.xml',
        'views/user_profile_content_details.xml',
    ],
    'installable': True,
    'application': False,
}
