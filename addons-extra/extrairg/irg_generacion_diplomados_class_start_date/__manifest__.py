# -*- coding: utf-8 -*-
{
    'name': 'Fecha de inicio de clases en diplomados',
    'version': '16.0.1.0.0',
    'summary': 'Usa date_start_class del lote en diplomas de diplomados y regenera el PDF al descargar.',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_generacion_diplomados',
        'isep_data_master_make',
        'irg_generacion_diplomados_website_verify',
        'irg_diplomado_portal_request',
        'irg_campus_diplomados_portal',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
