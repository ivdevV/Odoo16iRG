# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Certificados Isep',
    'summary': """Certificados Isep""",
    'description': """
    - Certificados Isep
    """,
    'version': '1.1.3',
    'author': 'silvau',
    'website': 'https://www.isep.es/contacto/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'web',
        'portal',
        'account',
        'openeducat_core',
        'openeducat_admission',
        'isep_documents_portal',
        'isep_student_migration',
        'isep_student_filter',
    ],
    'external_dependencies':{'python': [
      'base64','json','zlib','hashlib','cryptography','ssl','subprocess','tempfile'
     ],
    },
    'installable': True,

    'assets': {
        'web.report_assets_pdf': [

            '/isep_openeducat_reports/static/src/scss/custom_report_styles.scss',
            '/isep_openeducat_reports/static/src/img/background.png',
            '/isep_openeducat_reports/static/src/img/firmaluis.png',

        ],
        'web.assets_frontend': [

            '/isep_openeducat_reports/static/src/scss/custom_report_styles.scss',
            '/isep_openeducat_reports/static/src/img/background.png',
            '/isep_openeducat_reports/static/src/img/firmaluis.png',
            '/isep_openeducat_reports/static/src/img/firma_isep.png',
            '/isep_openeducat_reports/static/src/img/sello_isep.png',

        ],

     },

    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/data.xml',
        'wizards/diplomas_certifies_wizard.xml',
        'views/op_student_view.xml',
        'views/op_sign_certificate_view.xml',
        'views/ir_attachment_view.xml',
        'views/ir_actions_report_view.xml',
        'views/res_config_settings_view.xml',
        'views/certificates_portal_templates.xml',
        'reports/certified_diploma.xml',
        'reports/certificado1.xml',
        'reports/certificado2.xml',
        'reports/certificado3.xml',
        'reports/certificado4.xml',
        'reports/certificado5.xml',
        'reports/certificado6.xml',
        'reports/certificado8.xml',
    ]
}
