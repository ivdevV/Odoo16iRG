# -*- coding: utf-8 -*-
{
    'name': 'NLEX Grade Exemption',
    'version': '16.0.1.1.0',
    'summary': 'Excludes subjects with NLEX code from grades, certificates, and DEC export.',
    'description': """
        Excludes subjects with NLEX code from:
        - Validation checks in app.gradebook.student state_to_done
        - Total final average calculations
        - General average (avg_score) calculations
        - DEC exports (dec.document and dec.asignatura)
        - Current quarter average calculations
        - Report and Diploma printouts
    """,
    'author': 'iRG',
    'category': 'Education',
    'depends': [
        'isep_gradebook',
        'isep_control_escolar',
        'dec_document',
        'isep_openeducat_reports',
        'l10n_mx_edi_extended',
        'irg_gradebook_certificates',
    ],
    'data': [
        'views/report_gradebook.xml',
        'views/certified_diploma.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
