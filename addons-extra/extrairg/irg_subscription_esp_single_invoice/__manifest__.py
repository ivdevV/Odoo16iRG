{
    "name": "IRG Subscription ESP Single Invoice",
    "version": "16.0.1.0.0",
    "summary": "Single invoice subscription strategy with future installment adjustments",
    "category": "Sales/Subscriptions",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": [
        "sale_subscription",
        "isep_sale_subscription_extension",
        "irg_sale_subscription_esp",
        "isep_sale_order_cron_payment",
        "irg_payment_stripe_recurring"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        "views/stripe_event_views.xml",
        "views/subscription_adjustment_views.xml",
        "wizards/subscription_adjustment_wizard_views.xml"
    ],
    "installable": True,
    "application": False
}