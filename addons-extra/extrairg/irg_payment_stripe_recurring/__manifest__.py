{
    'name': 'IRG - Stripe Recurring Payments',
    'version': '16.0.2.0.0',
    'category': 'Accounting/Payment',
    'summary': 'Cobros recurrentes con Stripe: tokens, suscripciones reales y webhooks',
    'description': """
        Extiende payment_stripe para:
        - Asignar automáticamente el token Stripe a la suscripción tras el primer pago
        - Crear suscripciones reales en Stripe (POST /v1/subscriptions)
        - Sincronizar Customer y Price con Stripe API
        - Recibir webhooks de Stripe para eventos de suscripción
        - Cron de suspensión automática por cuotas vencidas impagadas
        - Cron de reactivación automática cuando se saldan deudas
        - Cron de reintento para suscripciones pendientes de creación
    """,
    'author': 'IRG',
    'website': 'https://www.irg.edu.es',
    'depends': [
        'payment_stripe',
        'sale_subscription',
        'isep_sale_subscription_extension',
        'isep_payment_cron',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/config_data.xml',
        'data/cron_data.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
