{
    'name': "Isep - Sale Subscription Extension",
    'summary': "Extension for Sale Subscription Custom",
    'description': """
        Moved changes from isep_sale_subscription_custom to a new module.
    """,
    'author': "Unknown",
    'category': 'Sales',
    'version': '16.0.1.0.0',
    'depends': ['base', 'sale', 'sale_subscription', 'sales_team', 'account', 'web', 'report_xlsx', 'web_grid', 'isep_openeducat_sale', 'isep_website_sale_custom'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/product_subscription_schedule.xml',
        'views/sale_subscription_schedule.xml',
        'views/sale_order.xml',
        'views/product_product.xml',
        'views/account_move.xml',
        'views/schedule_add_invoice_wizard.xml',
        'views/wizard_date_due.xml',
        'wizards/sale_order_datefilter_view.xml',
        'reports/report.xml',
        'reports/report_template_cartera.xml',
        'reports/report_template_estado_cuenta.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'isep_sale_subscription_extension/static/src/js/grid_controller.js',            
            'isep_sale_subscription_extension/static/src/css/grid_style.css',
        ],
    },
    'installable': True,
    'application': False,
}
