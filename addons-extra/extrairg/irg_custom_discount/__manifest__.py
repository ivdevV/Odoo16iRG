{
    'name': 'IRG - Descuentos con Fórmula Personalizada',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Códigos de descuento con fórmulas personalizadas para el ecommerce',
    'description': """
        Permite crear programas de descuento con fórmulas Python personalizadas.
        Se integra con el flujo existente de códigos de descuento del ecommerce.

        Variables disponibles en la fórmula:
        - amount_untaxed: Total sin impuestos del pedido
        - amount_total: Total con impuestos del pedido
        - qty_total: Cantidad total de productos
        - line_count: Número de líneas del pedido

        Ejemplos de fórmula:
        - amount_untaxed * 0.10          → 10% de descuento
        - min(amount_untaxed * 0.15, 500) → 15% con tope de 500€
        - 100 if amount_untaxed > 1000 else 50 → 100€ si >1000, sino 50€
    """,
    'author': 'IRG',
    'depends': [
        'sale',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'views/irg_discount_program_views.xml',
        'views/irg_discount_table_views.xml',
        'views/website_cart_feedback.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
