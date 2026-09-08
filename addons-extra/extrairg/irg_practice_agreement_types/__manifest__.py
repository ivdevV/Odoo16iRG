# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Agreement Types',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Tipos de convenio marco (nacional e internacional) en centros de prácticas',
    'author': 'IRG',
    'website': 'https://institutoraimongaja.com',
    'license': 'LGPL-3',
    'depends': [
        'irg_practice_agreement_sign',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/practice_agreement_create_wizard_views.xml',
        'views/practice_center_views.xml',
        'views/practice_agreement_views.xml',
        'views/agreement_clauses_internacional.xml',
        'views/portal_agreement_templates.xml',
        'report/practice_agreement_report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
