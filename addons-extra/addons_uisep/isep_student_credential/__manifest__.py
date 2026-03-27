# -*- coding: utf-8 -*-
{
    'name': 'Estudiante Credencial',
    'version': '16.4',
    'summary': """ Módulo para las credenciales exclusivo ante Instituto Raimon Gaja """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['base', 'web', 'openeducat_core_enterprise', 'openeducat_admission', 'isep_record_request', 'website_slides'],
    "data": [
        "security/data.xml",
        "views/credential_templates.xml",
        "views/res_partner_views.xml",
        "views/slide_slide_views.xml",
        "views/slides.xml",
        "reports/report_credential.xml"
    ],

    'assets': {
        'web.report_assets_pdf': [
            'isep_student_credential/static/src/img/background_front.png',
        ],
        'web.assets_frontend': [
            'isep_student_credential/static/src/img/background_front.png',
        ]
    },
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
