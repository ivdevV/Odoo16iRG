# -*- coding: utf-8 -*-
{
    'name': 'Certificados de Asistencia (iRG)',
    'version': '16.0.1.0.0',
    'category': 'Academic',
    'summary': 'Módulo para solicitar certificados de asistencia a clases en directo por sesión individual.',
    'author': 'Antigravity / iRG',
    'depends': [
        'irg_gradebook_certificates',
        'irg_campus_certificates_portal',
        'irg_op_course_modality',
    ],
    'data': [
        'views/irg_certificate_request_views.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
