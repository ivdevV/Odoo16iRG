# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Agreement Specific',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Convenio específico internacional desde la solicitud de prácticas',
    'author': 'IRG',
    'website': 'https://institutoraimongaja.com',
    'license': 'LGPL-3',
    'depends': [
        'irg_practice_agreement_types',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'wizard/practice_agreement_specific_create_wizard_views.xml',
        'views/practice_request_views.xml',
        'views/practice_agreement_views.xml',
        'views/agreement_document_especifico_internacional.xml',
        'views/portal_agreement_templates.xml',
        'report/practice_agreement_report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
