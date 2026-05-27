# -*- coding: utf-8 -*-
{
    'name': 'iRG - Generación de Actas de TFM/TFG',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Generador de actas de evaluación para Trabajos Finales de Máster y Grado',
    'author': 'ISEP / iRG',
    'license': 'AGPL-3',
    'website': 'https://institutoraimongaja.com',
    'depends': [
        'base',
        'web',
        'website',
        'openeducat_core',
        'irg_generacion_diplomas',  # Para reutilizar ReportLab setup, fonts, logos
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/acta_wizard_views.xml',
        'views/acta_views.xml',
    ],
    'external_dependencies': {
        'python': ['reportlab', 'babel'],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
