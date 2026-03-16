# -*- coding: utf-8 -*-
{
    'name': 'IRG Website Checkout Fixes',
    'version': '16.0.1.0.0',
    'category': 'Website/eCommerce',
    'author': 'Instituto Raimon Gaju',
    'license': 'LGPL-3',
    'depends': [
        'website_sale',
    ],
    'data': [
        'views/website_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_website_checkout_fixes/static/src/css/checkout_fix.css',
        ],
    },
    'installable': True,
    'application': False,
    'summary': 'Fix cuotas vacías, label de factura y contraste de inputs en checkout',
    'description': '''
        Arreglseveral issues en la página /shop/address:
        - Rellenar valores de cuotas ({}  → número real)
        - Cambiar label "Nombre de quíen factura" a "Nombre en la Factura"
        - Mejorar contraste de inputs (fondo blanco)
        
        Ver: doc/micro-specs/2026-03-16-irg_website_checkout_fixes.md
    ''',
}
