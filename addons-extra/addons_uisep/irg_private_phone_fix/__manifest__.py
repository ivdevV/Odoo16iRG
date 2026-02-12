{
    'name': 'IRG Private Phone Fix',
    'version': '16.0.1.0.0',
    'summary': 'Elimina el ocultamiento de teléfonos con asteriscos',
    'description': """
        Este módulo revierte la funcionalidad de isep_private_phone que oculta
        los números de teléfono y móvil con asteriscos (password=True).
        Hace que los campos sean visibles para todos los usuarios.
    """,
    'author': 'IRG',
    'depends': ['isep_private_phone'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
