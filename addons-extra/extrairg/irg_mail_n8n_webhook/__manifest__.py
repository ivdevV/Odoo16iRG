# -*- coding: utf-8 -*-

{
    'name': 'IRG Mail n8n Webhook',
    'version': '16.0.1.2.0',
    'category': 'Technical',
    'summary': 'Redirige el correo saliente de Odoo a un webhook de n8n',
    'description': """
        Intercepts outgoing mail.mail deliveries and sends them to n8n through
        a secured webhook, keeping a technical retry queue for failures.
    """,
    'author': 'IRG',
    'website': 'https://www.irg.edu.es',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/config_data.xml',
        'data/cron_data.xml',
        'views/res_config_settings_views.xml',
        'views/irg_mail_n8n_delivery_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}