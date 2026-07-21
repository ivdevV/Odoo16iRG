# -*- coding: utf-8 -*-
{
    'name': 'IRG Partner Gender',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Visible partner gender and resolve gender for auto admission.',
    'description': """
        Exposes gender on the contact form and sale order admission tab.
        Resolves admission gender with cascade: sale order → partner →
        name/title heuristic → 'o', writing back to the partner when guessed.
    """,
    'author': 'iRG',
    'depends': [
        'irg_admission_gender_fix',
        'isep_sale_order_admissions',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
