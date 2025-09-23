# -*- coding: utf-8 -*-
{
    'name': 'Isep Invoice Due Reminders',
    'version': '16.1',
    'summary': """ Alertas por vencimiento de facturas de alumno por correo electrónico """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['account','portal', 'mail' ],
    'data': [
        "data/cron.xml",
        "data/templates_emails.xml",
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
