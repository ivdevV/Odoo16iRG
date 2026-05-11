# -*- coding: utf-8 -*-

{
    'name': 'IRG Student Scholarship Documents',
    'version': '16.0.1.1.0',
    'category': 'OpenEduCat',
    'summary': 'Gestiona tipo de beca y documentacion asociada del alumno',
    'description': """
        Adds scholarship document upload management for OpenEduCat scholarship
        types on
        student scholarship documentation on contacts, student profiles, and the
        student portal.
    """,
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'portal',
        'website',
        'openeducat_core',
        'openeducat_scholarship_enterprise',
        'openeducat_web',
        'isep_website_custom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/scholarship_security.xml',
        'views/scholarship_document_views.xml',
        'views/res_partner_views.xml',
        'views/op_student_views.xml',
        'views/portal_templates.xml',
        'data/portal_menu_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
