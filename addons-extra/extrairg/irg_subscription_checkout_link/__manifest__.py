# -*- coding: utf-8 -*-
{
    "name": "IRG Subscription Checkout Link",
    "version": "16.0.1.0.0",
    "category": "Sales/Subscriptions",
    "summary": "Public checkout link for subscription onboarding before manual admission",
    "author": "Instituto Raimon Gaja",
    "license": "LGPL-3",
    "depends": [
        "sale_subscription",
        "isep_sale_subscription_extension",
        "irg_sale_manual_confirmation_wizard",
        "irg_payment_stripe_recurring",
        "website",
        "payment",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template_data.xml",
        "views/sale_order_views.xml",
        "views/checkout_templates.xml",
    ],
    "installable": True,
    "application": False,
}
