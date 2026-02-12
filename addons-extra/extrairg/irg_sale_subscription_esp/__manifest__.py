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
        'isep_sale_subscription_extension',
        'isep_sale_subscription_custom',
        'isep_website_sale_custom',  # Dependencia para asegurar que nuestro controller override gana
    ],
    'data': [
        'data/product_data.xml',
        'views/cart_summary.xml',
    ],
    'installable': True,
    'auto_install': False,
}
