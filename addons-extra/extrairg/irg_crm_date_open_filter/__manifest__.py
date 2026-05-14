# -*- coding: utf-8 -*-
{
    'name': 'IRG CRM Fecha Reactivacion Filter',
    'version': '16.0.1.0.1',
    'category': 'Sales/CRM',
    'summary': 'Adds fecha_reactivacion to CRM filters and lead list columns',
    'description': """
        Adds the crm.lead fecha_reactivacion field to the general search
        criteria and date filters for Leads and Opportunities, plus the
        optional list column for Leads.
    """,
    'author': 'IRG',
    'license': 'AGPL-3',
    'depends': ['crm', 'irg_crm_extensions'],
    'data': [
        'views/crm_lead_search_views.xml',
    ],
    'installable': True,
    'application': False,
}