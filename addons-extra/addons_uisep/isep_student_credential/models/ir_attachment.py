# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    is_image = fields.Boolean(string="Es imagen", compute="_compute_is_image", store=False)


    @api.depends('mimetype')
    def _compute_is_image(self):
        for at in self:
            at.is_image = (at.mimetype or '').startswith('image/')


    def use_profile_picture(self):
        self.ensure_one()
        if not self.is_image:
            raise UserError("El adjunto no es una imagen.")

        partner = self.partner_id
        if not partner:
            raise UserError("Este adjunto no está vinculado a un contacto.")

        if not self.datas:
            raise UserError("La imagen no tiene datos binarios.")

        partner.image_1920 = self.datas
