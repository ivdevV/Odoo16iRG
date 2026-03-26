# -*- coding: utf-8 -*-
{
    'name': 'IRG - Tipos de Identificación',
    'summary': 'Restringe los tipos de identificación a: DNI, Pasaporte, Documento Identificativo',
    'version': '16.0.1.0.0',
    'category': 'Hidden',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['l10n_latam_base'],
    'data': [
        'data/identification_types.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
