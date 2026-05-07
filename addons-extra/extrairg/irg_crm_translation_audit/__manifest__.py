# -*- coding: utf-8 -*-
{
    'name': 'IRG CRM Translation Audit',
    'version': '16.0.1.0.0',
    'category': 'CRM',
    'summary': 'Auditor de traducciones cargadas para CRM',
    'author': 'IRG',
    'license': 'AGPL-3',
    'depends': ['crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_translation_audit_views.xml',
    ],
    'installable': True,
    'application': False,
}
