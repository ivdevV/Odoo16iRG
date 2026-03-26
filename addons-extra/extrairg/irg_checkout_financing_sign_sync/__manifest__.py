# -*- coding: utf-8 -*-
{
    'name': 'IRG - Checkout Financing & Sign Sync',
    'version': '16.0.1.0.0',
    'category': 'Sales/Website',
    'summary': 'Sincroniza financiación en checkout y datos de matrícula para firma',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_sale_subscription_esp',
        'isep_website_sale_custom',
        'irg_migration_fields',
        'base_vat_optional_vies',
    ],
    'data': [
        'views/cart_summary_fix.xml',
        'views/address_fields_move.xml',
        'views/extra_info_fields_fix.xml',
        'views/post_payment_upload.xml',
        'views/registration_report_fix.xml',
        'views/sale_order_academic_attachments.xml',
    ],
    'installable': True,
    'auto_install': False,
}
