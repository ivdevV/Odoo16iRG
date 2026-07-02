{
    'name': 'IRG CRM Phone No Format',
    'version': '16.0.1.0.0',
    'summary': 'Desactiva el formateo automático y espacios en números de teléfono de Iniciativas (crm.lead)',
    'description': """
IRG CRM Phone No Format
========================
Este módulo desactiva por completo el formateo de teléfonos y móvil para el modelo crm.lead.
Evita la inserción automática de espacios y la alteración de prefijos tanto en backend como en frontend.
    """,
    'author': 'IRG',
    'depends': ['crm', 'phone_validation'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
