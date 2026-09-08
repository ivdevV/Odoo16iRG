# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Request Online Types',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Limita tipos de práctica en solicitudes de másteres online',
    'description': """
Para matrículas cuyo lote es máster online, el alumno portal solo puede
elegir convalidación por experiencia, convalidación por TFM o prácticas
asíncronas. Staff no está limitado.
    """,
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
        'isep_practices_2',
        'irg_practice_center_type_modalities',
        'irg_practice_preferred_quarter',
    ],
    'data': [
        'views/practice_request_portal_templates.xml',
    ],
    'installable': True,
    'application': False,
}
