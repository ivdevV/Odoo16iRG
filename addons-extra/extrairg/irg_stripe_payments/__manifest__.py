# -*- coding: utf-8 -*-
{
    'name': 'IRG - Stripe Payments Ledger',
    'version': '16.0.1.1.0',
    'category': 'Accounting/Payment',
    'summary': 'Listado de pagos de Stripe por contacto/alumno, con vinculación de identidad auditable.',
    'description': """
        Mantiene un registro local (ledger) de TODOS los pagos de Stripe y lo vincula
        al contacto de Odoo correspondiente.

        Cubre el hueco de la integración existente: los pagos sueltos
        (Payment Links de pago único, cobros del Dashboard, Checkout puntual,
        Terminal) llegan como 'payment_intent.succeeded' SIN factura de Stripe y
        hoy se descartan en silencio, por lo que no hay nada que listar.

        Características:
        - Modelo irg.stripe.payment: ledger idempotente de pagos Stripe.
        - Handlers de payment_intent.succeeded / payment_intent.payment_failed /
          charge.refunded / checkout.session.completed sobre el webhook firmado ya
          existente en /stripe/webhook (no crea un endpoint nuevo).
        - Resolución de identidad endurecida: ante email ambiguo NO adivina, encola
          para revisión manual en irg.stripe.identity.review.
        - Backfill histórico paginando el endpoint 'charges' de Stripe.
        - Listado en la ficha del contacto, en la del alumno y en menú propio.

        INVARIANTE: irg.stripe.payment es un ledger de SOLO LECTURA. Nunca escribe
        sale.note.inv.legacy, nunca toca sale.subscription.schedule, nunca crea
        account.move ni account.payment, nunca muta campos de dinero de sale.order.
        La conciliación monetaria sigue siendo exclusiva de _sync_invoice_paid /
        _register_paid_invoice_on_schedule en irg_stripe_subscriptions.
    """,
    'author': 'IRG',
    'website': 'https://www.irg.edu.es',
    'depends': [
        'irg_stripe_subscriptions',
        'openeducat_core',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        'views/irg_stripe_payment_views.xml',
        'views/irg_stripe_identity_review_views.xml',
        'wizard/irg_stripe_backfill_wizard_views.xml',
        'wizard/irg_stripe_identity_link_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/op_student_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
