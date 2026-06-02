# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PracticeCenter(models.Model):
    _inherit = 'practice.center'

    document_display_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='irg_practice_center_attachment_rel',
        column1='practice_center_id',
        column2='attachment_id',
        string='Displayed Center Documents',
        copy=False,
        readonly=True,
        help='Documents associated with this practice center.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        centers = super().create(vals_list)
        centers._normalize_document_attachments()
        return centers

    def write(self, vals):
        result = super().write(vals)
        if 'document_ids' in vals:
            self._normalize_document_attachments()
        return result

    def _normalize_document_attachments(self):
        for center in self:
            attachments = center.document_ids.filtered(
                lambda attachment: (
                    not attachment.res_model
                    or attachment.res_model == center._name
                )
                and not attachment.res_id
            )
            if attachments:
                attachments.write({
                    'res_model': center._name,
                    'res_id': center.id,
                })
