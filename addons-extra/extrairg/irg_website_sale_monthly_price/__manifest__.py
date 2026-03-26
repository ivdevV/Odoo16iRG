{
    'name': 'IRG Website Sale Monthly Price',
    'version': '16.0.1.0.0',
    'summary': 'Display monthly price for subscription products (IRG)',
    'category': 'Website/Website',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': ['website_sale', 'product', 'irg_website_sale_custom', 'website_sale_subscription'],
    'data': [
        'views/product_price_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_website_sale_monthly_price/static/src/js/website_sale_monthly.js',
            'irg_website_sale_monthly_price/static/src/css/form-visibility.css',
        ],
    },
    'installable': True,
    'application': False,
}
