# -*- coding: utf-8 -*-
{
    'name': 'Isep Op Academic Year',
    'version': '16.2',
    'summary': """ Módulo para gestionar años académicos y términos en Odoo.""",
    'description': """ Este módulo extiende las funcionalidades de gestión académica en Odoo""",
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['isep_openeducat_sale', 'openeducat_core', 'isep_sale_order_admissions'],
    "data": [
        "views/op_academic_term_views.xml"
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
