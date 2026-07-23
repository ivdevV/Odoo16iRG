{
    'name': 'ISEP OpenEducat Sale Lote Custom',
    'version': '16.0.1.1.0',
    'category': 'Sales',
    'summary': 'Customization for Lot Generation in Sale Orders',
    'description': """
        This module extends isep_openeducat_sale_lote to customize the lot code generation:
        - Removes prefix_06 (Language code)
        - Updates Modalidad code mapping:
            - Online -> ONL
            - HomeClass -> HC
            - Presencial -> PRS
            - Intensivo -> IN
        - Adds irg_is_intensive boolean field to sale.order and sale.order.line
    """,
    'author': 'Instituto Raimon Gaja',
    'depends': ['isep_openeducat_sale_lote', 'isep_data_master_make'],
    'data': [
        'views/op_batch_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
