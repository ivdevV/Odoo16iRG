# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


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

    def _check_admission_admin(self):
        if not self.env.is_superuser() and not self.env.user.has_group(
            'openeducat_admission.group_op_admission_admin'
        ):
            raise AccessError(_(
                'Solo los administradores de admisiones pueden enviar oficialidad.'
            ))

    @api.model
    def default_get(self, fields_list):
        self._check_admission_admin()
        values = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        if active_id:
            if active_model != 'op.admission.register':
                raise UserError(_(
                    'El asistente de oficialidad debe abrirse desde un registro '
                    'de admisión.'
                ))
            register = self.env['op.admission.register'].browse(active_id).exists()
            if register:
                values.update({
                    'register_id': register.id,
                    'admission_ids': [(6, 0, register.admission_ids.ids)],
                })
        return values

    def action_send(self):
        self.ensure_one()
        self._check_admission_admin()
        register = self.register_id.exists()
        if not register:
            raise UserError(_('El registro de admisión ya no existe.'))
        register.check_access_rights('read')
        register.check_access_rule('read')
        admissions = self.admission_ids.exists()
        if not admissions:
            raise UserError(_('Seleccione al menos una admisión para enviar.'))
        admissions.check_access_rights('read')
        admissions.check_access_rule('read')
        admissions.check_access_rights('write')
        admissions.check_access_rule('write')
        if any(admission.register_id != register for admission in admissions):
            raise UserError(_(
                'Todas las admisiones seleccionadas deben pertenecer al registro '
                'de admisión abierto.'
            ))
        self.env['irg.oficialidad.webhook.service'].send_oficialidad(
            register,
            admissions,
        )
        admissions.write({
            'oficialidad_sent_date': fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Oficialidad enviada'),
                'message': _(
                    'Se enviaron correctamente %(count)s admisiones.'
                ) % {'count': len(admissions)},
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
