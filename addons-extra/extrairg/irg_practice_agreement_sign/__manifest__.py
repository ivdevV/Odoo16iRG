# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Agreement Sign',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestión y firma digital de convenios marco con centros de prácticas',
    'description': """
        Módulo para la generación de plantillas de convenios marco con centros de prácticas,
        envío de enlaces públicos tokenizados para la cumplimentación de datos por parte del
        centro y captura de firma digital. Genera el PDF final del convenio con la firma de iRG
        y la del centro colaborador.
    """,
    'author': 'IRG',
    'website': 'https://institutoraimongaja.com',
    'license': 'LGPL-3',
    'depends': [
        'isep_practices_2',
        'irg_practice_center_documents',
        'portal',
        'mail',
    ],
    'data': [
        'security/practice_agreement_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/practice_agreement_views.xml',
        'views/practice_center_views.xml',
        'views/portal_agreement_templates.xml',
        'report/practice_agreement_report.xml',
        'report/practice_agreement_report_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
