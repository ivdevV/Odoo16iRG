# -*- coding: utf-8 -*-
{
    'name': 'IRG Pedido de Matrícula (editable)',
    'version': '16.0.1.0.0',
    'summary': 'Añade el reporte editable de Pedido de Matrícula para sale.order',
    'author': 'Antigravity',
    'category': 'Sale',
    'depends': [
        'irg_sale_order_extended',
    ],
    'data': [
        'reports/registration_order_editable_paperformat.xml',
        'reports/registration_order_editable_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
