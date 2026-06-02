# -*- coding: utf-8 -*-

{
    'name': 'IRG Welcome Diplomado Template Selector',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Ruteo de bienvenida para Diplomados con plantilla editable propia',
    'author': 'Instituto Raimon Gaja',
    'license': 'LGPL-3',
    'depends': [
        'irg_sale_manual_confirmation_wizard',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/auto_admission_required_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
