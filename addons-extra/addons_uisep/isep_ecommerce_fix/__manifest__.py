# -*- coding: utf-8 -*-
{
    'name': 'Ecommerce Fix',
    'version': '16.2',
    'summary': """ Modulo que hereda de isep_openeducat_sale y  isep_website_sale_custom, agrega condicionante al producto en el ecommerce""",
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['base', 'isep_openeducat_sale', 'isep_website_sale_custom'],
    "data": [
        "views/product_template_views.xml",
        "views/template_extra_info.xml",
        "views/template.xml",
    ],

    'assets': {
        'web.assets_frontend': [
            'isep_ecommerce_fix/static/src/components/website_sale_payment_inherit/website_sale_payment_inherit.js',
        ]
    },
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
