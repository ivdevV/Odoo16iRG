# -*- coding: utf-8 -*-
{
    'name': 'IRG Diploma Gradebook Template Weighting',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Activa la ponderacion 50/50 de diplomados mediante template.',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_diploma_gradebook_weighting',
        'irg_gradebook_editable_template',
        'isep_openeducat_sale',
    ],
    'data': [
        'data/gradebook_template_data.xml',
        'views/app_gradebook_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
