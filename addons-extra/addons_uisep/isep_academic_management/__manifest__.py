# -*- coding: utf-8 -*-
{
    'name': 'Isep Academic Management',
    'version': '1.6.1',
    'summary': """Bring all the academic management tools into one place""",
    'author': 'silvau',
    'category': 'tools',
    'depends': [
                 'web',
                 'openeducat_admission',
                 'openeducat_core',
                 'isep_elearning_custom',
                 'isep_control_escolar',
                 'isep_record_request_extended',
               ],
    'data': [
        'data/ir_sequence_data.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/academic_management_views.xml',
        "views/student_report_views.xml",
    ],


    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
