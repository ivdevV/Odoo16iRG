{
    'name': 'IRG CRM Reactivación',
    'version': '16.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Campos de reactivación para leads y oportunidades CRM',
    'description': """
        Agrega 4 campos de reactivación al modelo crm.lead:
        - Fecha de Reactivación
        - Campaña de Reactivación
        - Fuente de Reactivación
        - Referido de Reactivación
    """,
    'author': 'IRG',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_reactivacion.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
