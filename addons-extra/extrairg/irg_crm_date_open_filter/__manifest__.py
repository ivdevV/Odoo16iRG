# -*- coding: utf-8 -*-
{
    'name': 'IRG CRM Date Open Filter',
    'version': '16.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Adds date_open to CRM lead and opportunity filters and list columns',
    'description': """
        Adds the native crm.lead date_open field to the general search
        criteria, date filters, and optional list columns for Leads and
        Opportunities.
    """,
    'author': 'IRG',
    'license': 'AGPL-3',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_search_views.xml',
    ],
    'installable': True,
    'application': False,
}