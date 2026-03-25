# -*- coding: utf-8 -*-
{
    'name': 'IRG Timetable CSV Import',
    'version': '16.0.1.0.0',
    'summary': (
        'Importa sesiones académicas desde CSV depositados en un directorio vigilado. '
        'Mapea etiquetas de programa → curso/lote de Odoo y crea op.session '
        'con deduplicación automática.'
    ),
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['openeducat_timetable'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/program_map_views.xml',
        'views/import_log_views.xml',
        'views/menu.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
