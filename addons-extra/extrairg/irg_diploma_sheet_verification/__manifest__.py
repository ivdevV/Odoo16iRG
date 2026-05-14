# -*- coding: utf-8 -*-

{
    'name': 'IRG Diploma Sheet Verification',
    'version': '16.0.1.1.0',
    'category': 'Education',
    'summary': 'Verifica diplomas por QR en Odoo con fallback a Google Sheet',
    'description': """
        Public diploma verification page for QR codes. It checks Odoo diploma
        registry first and falls back to the historical Google Sheet CSV.
    """,
    'author': 'ISEP / iRG',
    'license': 'AGPL-3',
    'depends': [
        'website',
        'irg_generacion_diplomas',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'views/diploma_action_views.xml',
        'views/diploma_verify_templates.xml',
    ],
    'installable': True,
    'application': False,
}
