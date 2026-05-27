{
    'name': 'IRG - Sale Subscription Payment Terms',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Ajuste del cronograma de suscripción según las condiciones de pago',
    'description': """
        Ajusta las fechas de vencimiento de las cuotas del cronograma de pagos de suscripción
        usando las fechas calculadas por las condiciones de pago en lugar de un desfase fijo mensual.
    """,
    'author': 'Antigravity',
    'depends': [
        'sale',
        'sale_subscription',
        'isep_sale_subscription_extension',
        'isep_sale_subscription_custom',
        'account_payment_term_extension',
        'irg_subscription_esp_single_invoice',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
