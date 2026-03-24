# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IrgCertificateSentWizard(models.TransientModel):
    _name = 'irg.certificate.sent.wizard'
    _description = 'Asistente: Marcar Certificado como Enviado'

    certificate_id = fields.Many2one(
        'irg.certificate.request',
        string='Certificado',
        required=True,
        readonly=True,
    )
    tracking_number = fields.Char(string='Número de Seguimiento / Tracking')
    delivery_date = fields.Datetime(
        string='Fecha de Envío',
        default=fields.Datetime.now,
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        cert = self.certificate_id
        if cert.state != 'in_process':
            raise UserError(
                _('El certificado debe estar "En Proceso" para marcarse como enviado.')
            )
        cert.write({
            'state': 'sent',
            'delivery_date': self.delivery_date,
            'tracking_number': self.tracking_number or cert.tracking_number,
        })
        cert._send_sent_notification()
        return {'type': 'ir.actions.act_window_close'}
