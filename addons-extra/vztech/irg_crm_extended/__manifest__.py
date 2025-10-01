# -*- coding: utf-8 -*-
{
    'name': 'IRG CRM Extendido',
    'version': '0.1',
    'description': """Extends the functionalities of the CRM""",
    'author': "DFVZ TECH",
    'website': "https://vztech.odoo.com/",
    'category': 'CRM',
    'depends': [
        'base',
        'crm',
    ],
    'data': [
        'views/crm_lead_views.xml',
        'security/access_current_commercial.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
