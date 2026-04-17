{
    'name': 'IRG Portal Placeholder Safe',
    'version': '16.0.1.0.0',
    'summary': 'Garantiza placeholders seguros en el portal para evitar errores JS',
    'description': """
        Añade valores por defecto y placeholders invisibles para evitar
        errores `Cannot set properties of null (setting 'textContent')`
        cuando el portal intenta actualizar badges basados en
        `data-placeholder_count`.
    """,
    'author': 'IRG',
    'category': 'Website',
    'depends': ['portal'],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
