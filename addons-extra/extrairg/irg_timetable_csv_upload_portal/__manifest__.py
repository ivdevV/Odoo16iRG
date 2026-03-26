# -*- coding: utf-8 -*-

{
    'name': 'Upload Web de Calendarios',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'author': 'Instituto Raimón Gaja',
    'license': 'OPL-1',
    'depends': [
        'website',
        'web',
        'irg_timetable_csv_import',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/csv_upload_views.xml',
        'views/portal_upload_template.xml',
    ],
    'installable': True,
    'auto_install': False,
}
