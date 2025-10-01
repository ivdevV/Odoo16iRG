# -*- coding: utf-8 -*-
{
    'name': "Comisión por Mensualidades Affiliate Manager",

    'summary': """
        Modificaciones al modulo affiliate_management para incluir comisiones por mensualidad""",

    'description': """
        Modificaciones al modulo affiliate_management para incluir comisiones por mensualidad
    """,

    'author': "JPHA",
    'category': 'Website',
    'version': '0.1',


    'depends': ['base', 'affiliate_management'],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/action_sale_order_commission.xml',
        'views/views_affiliate_management.xml'
    ],

}
