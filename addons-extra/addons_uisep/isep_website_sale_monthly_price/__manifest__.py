{
    'name': 'ISEP Website Sale Monthly Price',
    'version': '16.0.1.0.0',
    'summary': 'Display monthly price for subscription products based on "Planes" attribute',
    'category': 'Website/Website',
    'author': 'ISEP',
    'license': 'LGPL-3',
    'depends': ['website_sale', 'product', 'isep_website_sale_custom', 'website_sale_subscription'],
    'data': [
        'views/product_price_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'isep_website_sale_monthly_price/static/src/js/website_sale_monthly.js',
        ],
    },
    'installable': True,
    'application': False,
}
