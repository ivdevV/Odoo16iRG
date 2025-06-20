# -*- coding: utf-8 -*-
{
    'name': 'Isep Website Sale Custom Address',
    'version': '16.1',
    'summary': """ Isep website sale custom Summary """,
    'author': 'Breithner Aquituari',
    'website': '',
    'category': 'Website',
    'depends': ['base', 'website_sale', 'sale_temporal', 'isep_sign_sale', 'sign', 'product', 'sale' ],
    "data": [
        "views/template.xml",
        "views/sale_temporal_recurrence_views.xml",
        "views/product_template_attribute_value_views.xml",
        "views/crm_team_views.xml",
        "data/automated_actions.xml",
        "data/mail_template.xml",
        "views/sale_order_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
