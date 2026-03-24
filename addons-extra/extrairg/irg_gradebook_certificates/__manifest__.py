# -*- coding: utf-8 -*-
{
    'name': 'IRG Gradebook Certificates',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Solicitud y generación de certificados de notas (backend y portal con pago)',
    'description': """
        Permite generar certificados de notas de dos formas:

        Backend (admin/docente): wizard directo → PDF descargado al instante.
        Portal (alumno): solicitud con pago vía website_sale.

        Tipos:
          - Certificado de Notas Digital (30 €)
          - Certificado de Notas Físico (40 € + envío)
          - Certificado de Notas a Medida (40 €)
          - Certificado de Notas Físico Apostillado (80 € + envío)

        Envío Nacional: +20 € | Envío Internacional: +60 €
    """,
    'author': 'ISEP / iRG',
    'website': 'https://institutoraimongaja.com',
    'depends': [
        'isep_gradebook',
        'website_sale',
        'sale',
        'portal',
        'mail',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequence_data.xml',
        'data/product_data.xml',
        'data/mail_templates.xml',
        'views/irg_certificate_request_views.xml',
        'views/app_gradebook_student_views.xml',
        'views/menu.xml',
        'wizard/certificate_wizard_views.xml',
        'report/reports.xml',
        'report/certificate_templates.xml',
        'views/portal_certificate_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
