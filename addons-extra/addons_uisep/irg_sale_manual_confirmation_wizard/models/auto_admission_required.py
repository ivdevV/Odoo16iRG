# -*- coding: utf-8 -*-
from odoo import models, fields


class AutoAdmissionRequired(models.Model):
    _inherit = 'auto.admission.required'

    manual_wizard_enabled = fields.Boolean(
        string="Activar routing email por modalidad (Online/HC)",
        default=True,
        help="Si esta activo, el email de bienvenida se elige por el codigo "
             "del lote (ONL -> plantilla online, resto -> plantilla por defecto). "
             "Si esta desactivado, se respeta la logica existente."
    )

    welcome_template_online_id = fields.Many2one(
        comodel_name='mail.template',
        string="Plantilla bienvenida Online",
        domain="[('model','=','op.admission')]",
        help="Plantilla usada cuando el lote es Online (codigo contiene 'ONL'). "
             "Por defecto irg_elearning_correo_bienvenida_selector."
             "email_op_admission_confirm_online si esta instalado."
    )

    welcome_template_default_id = fields.Many2one(
        comodel_name='mail.template',
        string="Plantilla bienvenida por defecto",
        domain="[('model','=','op.admission')]",
        help="Plantilla usada para HC / PRS / GE. Por defecto "
             "isep_elearning_custom.email_op_admission_confirm."
    )
