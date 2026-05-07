{
    'name': 'IRG Online Subject Opening',
    'version': '16.0.1.0.0',
    'summary': 'Calcula aperturas individuales de asignaturas online por admision',
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'isep_elearning_custom',
        'irg_subject_fix',
        'isep_subject_precedence',
        'website_slides',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/op_admission_views.xml',
        'templates/portal_subject_opening.xml',
    ],
    'installable': True,
    'application': False,
}
