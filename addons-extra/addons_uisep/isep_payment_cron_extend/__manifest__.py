# -*- coding: utf-8 -*-
{
    'name': 'Isep - Payments Cron Extends',
    'version': '16.2',
    'summary': """ Realizar cobros de clientes tokenizados mediante cron Extends""",
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['isep_payment_cron', 'isep_sale_subscription_custom'],
    "data": [
        "data/cron.xml",
        "security/group.xml",
        "security/ir.model.access.csv",
        "views/payment_retry_log_views.xml",
        "wizards/recurring_payment_wizard_cron.xml"
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
