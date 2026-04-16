# -*- coding: utf-8 -*-
{
    'name': 'IRG Portal Placeholder Count Fix',
    'version': '16.0.1.0.0',
    'summary': 'Previene errores JS en badges de contador del portal cuando faltan valores de placeholder_count.',
    'description': """
        Evita el fallo "Cannot set properties of null (setting 'textContent')"
        en el portal cuando existen badges con `data-placeholder_count`
        pero la clave correspondiente no se devuelve en los valores del portal.
    """,
    'author': 'IRG',
    'category': 'Website',
    'depends': [
        'portal',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
