# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OficialidadSendWizard(models.TransientModel):
    _name = 'oficialidad.send.wizard'
    _description = 'Enviar admisiones al webhook de oficialidad'

    register_id = fields.Many2one(
        'op.admission.register',
        string='Registro de admisión',
        readonly=True,
        required=True,
    )
    admission_ids = fields.Many2many(
        'op.admission',
        string='Admisiones',
        domain="[('register_id', '=', register_id)]",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            register = self.env['op.admission.register'].browse(active_id).exists()
            if register:
                values.update({
                    'register_id': register.id,
                    'admission_ids': [(6, 0, register.admission_ids.ids)],
                })
        return values

    def action_send(self):
        self.ensure_one()
        if not self.admission_ids:
            raise UserError(_('Seleccione al menos una admisión para enviar.'))
        self.env['irg.oficialidad.webhook.service'].send_oficialidad(
            self.register_id,
            self.admission_ids,
        )
        self.admission_ids.write({
            'oficialidad_sent_date': fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Oficialidad enviada'),
                'message': _(
                    'Se enviaron correctamente %(count)s admisiones.'
                ) % {'count': len(self.admission_ids)},
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
