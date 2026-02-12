{
    'name': 'IRG Phone Prefix Fix',
    'version': '16.0.1.0.0',
    'summary': 'Evita que se elimine el prefijo 1 en números de México (+52)',
    'description': """
        Este módulo modifica el comportamiento de formateo de telefonos para México.
        Por defecto, Odoo (y libphonenumber) eliminan el dígito "1" después del +52 
        porque está obsoleto. Este módulo lo restaura si el usuario lo introdujo,
        permitiendo formatos como +52 1 XXXXXXXXXX.
    """,
    'author': 'IRG',
    'depends': ['base', 'phone_validation'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
