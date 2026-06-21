# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def _map_partner_gender(self, partner):
        """Helper to map any res.partner gender value to ('m', 'f', 'o') format."""
        if not partner:
            return 'o'
        
        # Check both fields: gender (selection) and gender_type (moodle selection)
        gender_val = getattr(partner, 'gender', False)
        if not gender_val and hasattr(partner, 'gender_type'):
            gender_val = getattr(partner, 'gender_type', False)

        if gender_val in ('m', 'male', 'Male', 'Masculino'):
            return 'm'
        if gender_val in ('f', 'female', 'Female', 'Femenino'):
            return 'f'
        return 'o'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            partner = self.env['res.partner'].browse(partner_id) if partner_id else False
            
            incoming_gender = vals.get('gender')
            
            # Map input gender value if it's 'male'/'female'
            if incoming_gender in ('male', 'Male', 'Masculino'):
                vals['gender'] = 'm'
            elif incoming_gender in ('female', 'Female', 'Femenino'):
                vals['gender'] = 'f'
            elif incoming_gender in ('other', 'not-sure', 'Other', 'Otro'):
                vals['gender'] = 'o'
            # If gender is not provided, or is the default 'o', check the partner
            elif (not incoming_gender or incoming_gender == 'o') and partner:
                mapped_gender = self._map_partner_gender(partner)
                if mapped_gender in ('m', 'f'):
                    _logger.info("IRG Gender Fix: Mapping empty/default admission gender to partner's gender: %s -> %s", partner.name, mapped_gender)
                    vals['gender'] = mapped_gender
        return super(OpAdmission, self).create(vals_list)

    def write(self, vals):
        incoming_gender = vals.get('gender')
        
        if incoming_gender:
            if incoming_gender in ('male', 'Male', 'Masculino'):
                vals['gender'] = 'm'
            elif incoming_gender in ('female', 'Female', 'Femenino'):
                vals['gender'] = 'f'
            elif incoming_gender in ('other', 'not-sure', 'Other', 'Otro'):
                vals['gender'] = 'o'
        elif 'partner_id' in vals and 'gender' not in vals:
            partner = self.env['res.partner'].browse(vals['partner_id'])
            mapped_gender = self._map_partner_gender(partner)
            if mapped_gender in ('m', 'f'):
                _logger.info("IRG Gender Fix: Mapping admission gender on partner change: %s -> %s", partner.name, mapped_gender)
                vals['gender'] = mapped_gender

        return super(OpAdmission, self).write(vals)
