{
    'name': 'IRG Website Sale Monthly Default Combo',
    'version': '16.0.1.0.0',
    'summary': 'Align shop listing monthly price with product default combination',
    'category': 'Website/Website',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'isep_website_sale_monthly_price',
        'isep_website_sale_custom',
        'website_sale',
    ],
    'data': [
        'views/product_price_template.xml',
    ],
    'installable': True,
    'application': False,
}
