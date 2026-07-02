# -*- coding: utf-8 -*-
{
    'name': 'IRG Pedido de Matrícula RVOE',
    'version': '16.0.1.0.0',
    'summary': 'Añade el reporte de Pedido de Matrícula RVOE para sale.order',
    'author': 'Antigravity',
    'category': 'Sale',
    'depends': [
        'irg_sale_order_extended',
        'isep_openeducat_sale',
    ],
    'data': [
        'reports/registration_order_rvoe_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
