# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class PracticeAgreement(models.Model):
    _inherit = 'practice.agreement'

    agreement_type = fields.Selection(
        [
            ('marco_nacional', 'Convenio Marco Nacional'),
            ('marco_internacional', 'Convenio Marco Internacional'),
        ],
        string='Tipo de convenio',
        default='marco_nacional',
        tracking=True,
        index=True,
    )

    def write(self, vals):
        if 'agreement_type' in vals:
            locked = self.filtered(
                lambda rec: rec.state in ('sent', 'completed', 'cancelled')
            )
            if locked:
                raise UserError(
                    _('No se puede cambiar el tipo de un convenio ya enviado o firmado.')
                )
        return super().write(vals)

    def action_complete_signature(self, signature_base64, signer_name, ip_address=False):
        res = super().action_complete_signature(
            signature_base64, signer_name, ip_address
        )
        self.ensure_one()
        slug = (
            'Internacional'
            if self.agreement_type == 'marco_internacional'
            else 'Nacional'
        )
        center_name = self.center_official_name or self.practice_center_id.name
        new_name = 'Convenio_Marco_%s_%s_%s.pdf' % (slug, center_name, self.id)
        old_name = 'Convenio_Marco_%s_%s.pdf' % (center_name, self.id)
        if self.pdf_attachment_id:
            self.pdf_attachment_id.name = new_name
        center_att = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'practice.center'),
            ('res_id', '=', self.practice_center_id.id),
            ('name', '=', 'Convenio Firmado - %s' % old_name),
        ], limit=1)
        if center_att:
            center_att.name = 'Convenio Firmado - %s' % new_name
        return res
