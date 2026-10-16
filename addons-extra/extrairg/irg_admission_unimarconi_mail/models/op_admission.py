from odoo import _, api, fields, models
from odoo.exceptions import UserError

TEMPLATE_XMLID = (
    'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
)


def irg_batch_code_is_official_master(code):
    return (code or '').strip().upper().startswith('MO')


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    irg_show_unimarconi_mail = fields.Boolean(
        compute='_compute_irg_show_unimarconi_mail',
        string='Mostrar correo Unimarconi',
    )

    @api.depends('batch_id', 'batch_id.code')
    def _compute_irg_show_unimarconi_mail(self):
        for admission in self:
            code = admission.batch_id.code if admission.batch_id else ''
            admission.irg_show_unimarconi_mail = (
                irg_batch_code_is_official_master(code)
            )

    def action_send_unimarconi_mail(self):
        self.ensure_one()
        code = self.batch_id.code if self.batch_id else ''
        if not irg_batch_code_is_official_master(code):
            raise UserError(_(
                'El envío solo corresponde a lotes cuyo código empieza por MO.'
            ))
        if not (self.email or '').strip():
            raise UserError(_(
                'Indica el correo de la admisión antes de enviar la matrícula Unimarconi.'
            ))
        template = self.env.ref(TEMPLATE_XMLID, raise_if_not_found=False)
        if not template:
            raise UserError(_(
                'No está instalada la plantilla de matrícula Unimarconi.'
            ))
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        return {
            'name': _('Enviar matrícula Unimarconi'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': {
                'default_model': 'op.admission',
                'default_res_id': self.id,
                'default_use_template': True,
                'default_template_id': template.id,
                'default_composition_mode': 'comment',
                'force_email': True,
            },
        }
