{
    'name': 'IRG CRM Lead Deduplicator',
    'version': '16.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Cron diario para detectar y fusionar leads duplicados por email o teléfono',
    'author': 'IRG',
    'depends': ['crm'],
    'data': [
        'data/cron.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
