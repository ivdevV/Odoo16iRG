# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Adaptacion de Campos para IRG",
    "version": "16.0.1.0.1",
    "author": "FantasticoLab",
    "website": "https://www.fantasticolab.com",
    "category": "CRM",
    "license": "AGPL-3",
    "depends": [
        "base",
        "website_mail",
        "mail",
        "crm",
        "sale"
        #"voip",
        #"isep_custom",
        #"hspl_user_simulation",
    ],
    "data": [
         #"reports/registration_order_paperformat.xml",
         #"reports/registration_order_template.xml",
         "views/res_partner.xml",
         "views/crm_lead.xml",
    #     "views/voip_phonecall.xml",
    #
    ],
    "assets": {
        "web.report_assets_common":[
            "/irg_migration_fields/static/src/scss/opensans.scss",
            ],
        },
    'installable': True,
}
