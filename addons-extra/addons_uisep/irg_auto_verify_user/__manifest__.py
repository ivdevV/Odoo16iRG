# -*- coding: utf-8 -*-
{
    'name': 'IRG Auto Verify User',
    'version': '16.0.1.0.0',
    'summary': 'Auto-verifica las cuentas de usuario al crearlas',
    'description': """
        Este módulo auto-verifica las cuentas de usuario asignándoles
        karma automáticamente cuando se crean.
        
        Esto evita que aparezca el mensaje:
        "No se ha verificado su cuenta. Haga clic aquí para recibir 
        un correo de verificación!"
        
        El módulo website_profile de Odoo considera verificado a un
        usuario si tiene karma > 0. Este módulo asigna karma = 3
        (VALIDATION_KARMA_GAIN) automáticamente al crear usuarios.
    """,
    'author': 'IRG',
    'category': 'Website',
    'depends': [
        'base',
        'gamification',  # Este módulo define el campo karma en res.users
    ],
    'data': [
        'data/cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
