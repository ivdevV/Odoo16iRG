# -*- coding: utf-8 -*-
{
    'name': 'Portal Unificado de Certificaciones y Diplomas',
    'version': '16.0.1.0.0',
    'summary': 'Centraliza diplomas, actas de TFM/TFG y solicitudes de certificados de notas en el portal del campus.',
    'category': 'Website',
    'author': 'iRG',
    'depends': [
        'website',
        'portal',
        'irg_generacion_diplomas',
        'irg_gradebook_certificates',
        'irg_tfm_acta_documento',
        'isep_website_custom',
        'irg_course_portal_tiles',
    ],
    'data': [
        'views/portal_templates.xml',
        'views/campus_dashboard_override.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
