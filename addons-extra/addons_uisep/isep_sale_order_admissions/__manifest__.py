# -*- coding: utf-8 -*-
{
    'name': 'Isep Sale Order Admissions',
    'version': '16.6',
    'summary': """ Admissions for sale order """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['isep_openeducat_sale','isep_elearning_custom', 'isep_ecommerce_fix', 'isep_subject_precedence'],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml"
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
