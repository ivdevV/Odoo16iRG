# -*- coding: utf-8 -*-
{
    'name': 'IRG CRM Fecha Reactivacion Filter',
    'version': '16.0.1.0.1',
    'category': 'Sales/CRM',
    'summary': 'Adds reactivation fields to CRM filters and lead list columns',
    'description': """
        Adds CRM reactivation fields to the general search criteria for
        Leads and Opportunities, plus optional list columns for Leads.
    """,
    'author': 'IRG',
    'license': 'AGPL-3',
    'depends': ['crm', 'irg_crm_extensions', 'irg_crm_reactivacion'],
    'data': [
        'views/crm_lead_search_views.xml',
    ],
    'installable': True,
    'application': False,
}