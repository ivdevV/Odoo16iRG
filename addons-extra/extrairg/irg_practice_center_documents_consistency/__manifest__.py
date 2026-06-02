# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Center Documents Consistency',
    'version': '16.0.1.0.0',
    'summary': 'Estabiliza el guardado de documentos en centros de practicas',
    'description': """
        Corrige la consistencia de los adjuntos documentales asociados a
        centros de practicas separando el campo de carga del campo de
        visualizacion y normalizando la vinculacion de ir.attachment.
    """,
    'author': 'IRG',
    'category': 'Education',
    'depends': [
        'irg_practice_center_documents',
    ],
    'data': [
        'views/practice_center_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
