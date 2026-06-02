# -*- coding: utf-8 -*-
{
    'name': 'IRG Portal Invoice Hide Pay Now',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Oculta los botones de "Pagar ahora" del portal de facturas',
    'description': """
        Elimina la opción de pago online del portal de facturas para todos los usuarios.
        - Quita el botón "Pagar ahora" de la lista de facturas (/my/invoices)
        - Quita el botón "Pagar ahora" del detalle de factura
        - Quita el bloque de checkout de pago
    """,
    'author': 'iRG',
    'website': '',
    'depends': [
        'account',
        'account_payment',
        'account_payment_invoice_online_payment_patch',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
