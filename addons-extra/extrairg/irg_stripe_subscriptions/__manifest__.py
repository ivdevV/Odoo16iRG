# -*- coding: utf-8 -*-
{
    'name': 'IRG - Stripe Subscriptions and Payment Links Integration',
    'version': '16.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Suscripciones y Enlaces de Pago nativos de Stripe con sincronización en tiempo real.',
    'description': """
        Módulo para la sincronización y gestión de suscripciones nativas de Stripe y enlaces fijos de pago.
        
        Características principales:
        - Registro local de suscripciones Stripe (stripe.subscription).
        - Registro local de enlaces de pago Stripe (stripe.payment.link).
        - Historial de eventos y control de idempotencia (stripe.event.log).
        - Controlador para webhook firmado en /stripe/webhook.
        - Servicio de sincronización automática (stripe.sync).
        - Integración con el wizard de confirmación manual y el flujo de venta de Odoo.
    """,
    'author': 'IRG',
    'website': 'https://www.irg.edu.es',
    'depends': [
        'sale_subscription',
        'irg_payment_stripe_recurring',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/stripe_subscription_views.xml',
        'views/stripe_payment_link_views.xml',
        'views/stripe_event_log_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
