# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Agreement Specific',
    'version': '16.0.1.2.1',
    'category': 'Education',
    'summary': 'Convenios específicos nacional, internacional y HomeClass síncronas',
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
        'views/agreement_document_especifico_nacional.xml',
        'views/agreement_document_especifico_homeclass_sincronas.xml',
        'views/portal_agreement_templates.xml',
        'report/practice_agreement_report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
