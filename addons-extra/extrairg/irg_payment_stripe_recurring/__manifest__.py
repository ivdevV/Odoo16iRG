{
    'name': 'IRG - Stripe Recurring Payments',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Payment',
    'summary': 'Habilita cobros recurrentes con token Stripe para suscripciones IRG',
    'description': """
        Extiende payment_stripe para:
        - Asignar automáticamente el token Stripe a la suscripción tras el primer pago
        - Cron de suspensión automática por cuotas vencidas impagadas
        - Cron de reactivación automática cuando se saldan deudas
        
        NO modifica:
        - sale.subscription.schedule (modelo ni vistas)
        - create_subscription_schedule() ni _auto_scheduled_order()
        - El cron de cobro existente (isep_payment_cron)
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
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
