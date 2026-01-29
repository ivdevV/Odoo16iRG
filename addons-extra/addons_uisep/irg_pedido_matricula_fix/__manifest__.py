# -*- coding: utf-8 -*-
{
    'name': 'IRG Pedido Matrícula Fix',
    'version': '16.0.1.0.0',
    'summary': 'Corrige el cálculo de oficialidad en pedidos de matrícula',
    'description': """
        Este módulo extiende el cálculo del campo is_official en sale.order
        para que también considere si el nombre del producto contiene "oficial".
        
        Esto es útil para el ecommerce donde los productos con oficialidad
        pueden no tener el campo formation_type configurado como 'officialdom'.
    """,
    'author': 'IRG',
    'website': '',
    'category': 'Sales',
    'depends': [
        'sale',
        'irg_sale_order_extended',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
