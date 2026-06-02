# -*- coding: utf-8 -*-

from odoo import _, fields, models


class AutoAdmissionRequired(models.Model):
    _inherit = 'auto.admission.required'

    DIPLOMADO_TEMPLATE_NAME = 'Bienvenida admision Diplomados'

    welcome_template_diplomado_id = fields.Many2one(
        comodel_name='mail.template',
        string='Plantilla bienvenida Diplomados',
        domain="[('model','=','op.admission')]",
        help='Plantilla usada para admisiones cuyo lote o categoria empieza por DI.',
    )

    def action_irg_ensure_diplomado_welcome_template(self):
        """Create and assign the editable Diplomados welcome template.

        The method is safe to run on module updates: it never overwrites an
        existing copied template, so UI edits are preserved.
        """
        env = self.sudo().env
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
                return False

            diplomado_template = default_template.copy({
                'name': _(self.DIPLOMADO_TEMPLATE_NAME),
            })
            env['ir.model.data'].create({
                'module': module,
                'name': name,
                'model': 'mail.template',
                'res_id': diplomado_template.id,
                'noupdate': True,
            })

        current_name = diplomado_template.with_context(lang='en_US').name or ''
        if (
            self.DIPLOMADO_TEMPLATE_NAME not in current_name
            and ('(copy)' in current_name or '(copia)' in current_name.lower())
        ):
            diplomado_template.with_context(lang='en_US').write({
                'name': self.DIPLOMADO_TEMPLATE_NAME,
            })
            diplomado_template.with_context(lang='es_ES').write({
                'name': self.DIPLOMADO_TEMPLATE_NAME,
            })

        configs = env['auto.admission.required'].search([
            ('welcome_template_diplomado_id', '=', False),
        ])
        configs.write({'welcome_template_diplomado_id': diplomado_template.id})
        return True
