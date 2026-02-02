{
    'name': 'IRG CRM Extensions',
    'version': '16.0.1.0.2',
    'category': 'Sales/CRM',
    'summary': 'Extensiones personalizadas para el CRM de IRG',
    'description': """
        Extensiones personalizadas para el CRM de IRG.
        - Seguimiento del Comercial Anterior (last_user_id)
    """,
    'author': 'IRG',
    'depends': ['crm'],
    'data': [
        'views/crm_lead.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}