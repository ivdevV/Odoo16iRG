# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Adaptacion de Campos de Estudiantes de OpenEducat para IRG/UISEP",
    "version": "16.0.1.0.0",
    "author": "FantasticoLab",
    "website": "https://www.fantasticolab.com",
    "category": "CRM",
    "license": "AGPL-3",
    "depends": [
        "base",
        "website_mail",
        "mail",
        "crm",
        "sale",
        "irg_op_student_fields",
    ],
    "data": [
         "security/ir.model.access.csv",
         "views/op_student.xml",
         "views/res_partner.xml",
    #     "views/voip_phonecall.xml",
         "reports/pedido_matricula.xml",
    #
    ],
    'installable': True,
#    'post_init_hook': 'post_init_hook',
}
