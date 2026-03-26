{
    'name': 'IRG Website Sale Custom Address',
    'version': '16.0.1.0.0',
    'summary': 'Custom website sale address and hooks (IRG)',
    'author': 'IRG',
    'category': 'Website',
    'depends': ['base', 'website_sale', 'website_sale_subscription', 'product', 'sale'],
    'data': [
        'views/template.xml',
        'views/template_extra_info.xml',
        'views/sale_temporal_recurrence_views.xml',
        'views/product_template_attribute_value_views.xml',
        'views/crm_team_views.xml',
        'data/automated_actions.xml',
        'data/mail_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_website_sale_custom/static/src/js/address_toast.js',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
