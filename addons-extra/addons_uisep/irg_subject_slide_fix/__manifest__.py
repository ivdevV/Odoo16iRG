# -*- coding: utf-8 -*-
{
    'name': 'IRG Subject Slide Fix',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Fix para filtrar asignaturas activas y en lote en el panel de control del campus',
    'description': """
        Este módulo corrige el panel de control del campus virtual para que:
        1. Solo muestre las asignaturas que corresponden al lote (batch) del estudiante.
        2. Solo muestre como disponibles/activas las asignaturas donde el estudiante tiene un registro activo en
           slide.channel.partner (respetando las fechas del lote).
        
        El problema original era que user.partner_id.slide_channel_ids no filtraba
        por el campo active del modelo intermedio slide.channel.partner, y se mostraban
        todas las asignaturas del curso en lugar de solo las del lote.
    """,
    'author': 'IRG',
    'website': '',
    'depends': [
        'isep_website_custom',
        'website_slides',
    ],
    'data': [
        'views/user_profile_content_details.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
