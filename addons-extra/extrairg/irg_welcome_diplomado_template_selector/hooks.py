# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api, _


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = 'irg_welcome_diplomado_template_selector'
    name = 'email_op_admission_confirm_diplomado'

    model_data = env['ir.model.data'].search([
        ('module', '=', module),
        ('name', '=', name),
        ('model', '=', 'mail.template'),
    ], limit=1)
    diplomado_template = env['mail.template']
    if model_data:
        diplomado_template = env['mail.template'].browse(model_data.res_id).exists()

    if not diplomado_template:
        default_template = env.ref(
            'isep_elearning_custom.email_op_admission_confirm',
            raise_if_not_found=False,
        )
        if not default_template:
            return

        # Created with superuser during installation so users can edit it afterwards.
        diplomado_template = default_template.copy({
            'name': _('Bienvenida admision Diplomados'),
        })
        env['ir.model.data'].create({
            'module': module,
            'name': name,
            'model': 'mail.template',
            'res_id': diplomado_template.id,
            'noupdate': True,
        })

    configs = env['auto.admission.required'].search([
        ('welcome_template_diplomado_id', '=', False),
    ])
    configs.write({'welcome_template_diplomado_id': diplomado_template.id})
