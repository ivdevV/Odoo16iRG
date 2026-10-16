{
    'name': 'IRG Admission Unimarconi Mail',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Correo de matrícula Unimarconi en admisiones de máster oficial',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': ['openeducat_admission', 'mail'],
    'data': [
        'data/mail_template_data.xml',
        'views/op_admission_views.xml',
    ],
    'installable': True,
    'application': False,
}
