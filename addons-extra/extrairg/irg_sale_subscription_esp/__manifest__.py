{
    'name': 'IRG - Sale Subscription ESP',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Gestión de suscripciones y financiación para IRG',
    'description': """
        Rework del sistema de ecommerce y suscripciones.
        - Desglose automático de gastos de financiación basado en la diferencia con precio al contado.
        - Generación de líneas de servicio para financiación.
    """,
    'author': 'Odoo',
    'depends': [
        'sale',
        'website_sale',
        'sale_subscription',
        'isep_sale_subscription_extension',  # Dependencia para sobrescribir su lógica
    ],
    'data': [
        'data/product_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
