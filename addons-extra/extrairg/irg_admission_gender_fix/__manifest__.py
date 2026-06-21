# -*- coding: utf-8 -*-
{
    'name': 'IRG Admission Gender Fix',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Fixes contact to admission/student gender mapping conflicts.',
    'description': """
        Handles mapping res.partner gender values ('male', 'female', 'not-sure', etc.)
        to the expected op.admission and op.student selection values ('m', 'f', 'o')
        during creation and modification.
    """,
    'author': 'Antigravity / Google DeepMind',
    'depends': [
        'openeducat_admission',
        'openeducat_core',
    ],
    'data': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
