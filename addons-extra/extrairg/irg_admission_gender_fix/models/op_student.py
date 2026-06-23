# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import unicodedata

_logger = logging.getLogger(__name__)

class OpStudent(models.Model):
    _inherit = 'op.student'

    def _clean_string(self, s):
        if not s:
            return ''
        # Remove accents and normalize to lowercase
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
        return s.strip().lower()

    def _guess_gender(self, name, title_name=None):
        """Guess gender based on title and/or first name."""
        if title_name:
            title_clean = self._clean_string(title_name)
            for female_title in ('sra', 'mrs', 'ms', 'dna', 'dona', 'dra', 'senora'):
                if female_title in title_clean:
                    return 'f'
            for male_title in ('sr', 'mr', 'don', 'senor', 'dr'):
                if male_title in title_clean:
                    return 'm'

        if not name:
            return 'o'

        parts = name.split()
        if not parts:
            return 'o'
        first_name = self._clean_string(parts[0])

        female_names = {
            'maria', 'ana', 'carmen', 'josefa', 'isabel', 'marta', 'sara', 'ana maria', 'maria carmen',
            'laura', 'cristina', 'pilar', 'antonia', 'dolores', 'teresa', 'francisca', 'elena', 'patricia',
            'monica', 'alicia', 'rosa', 'beatriz', 'julia', 'silvia', 'raquel', 'irene', 'clara', 'lorena',
            'vanesa', 'angela', 'mercedes', 'rocio', 'gemma', 'olga', 'eva', 'paula', 'alba', 'noelia',
            'sofia', 'miriam', 'estela', 'mar', 'nieves', 'concepcion', 'juana', 'luisa', 'manuela',
            'margarita', 'gloria', 'amparo', 'lourdes', 'inmaculada', 'virginia', 'susana', 'yolanda',
            'esther', 'rebeca', 'nuria', 'loreto', 'begona', 'arancha', 'nerea', 'itziar', 'amaia',
            'ainhoa', 'leire', 'maite', 'estefania', 'andrea', 'belen', 'ines', 'montserrat', 'lucia',
            'gabriela', 'valeria', 'daniela', 'camila', 'mariana', 'regina', 'ximena', 'jimena',
            'renata', 'victoria', 'sandra', 'paola', 'claudia', 'diana', 'veronica', 'adriana', 'leticia'
        }

        male_names = {
            'jose', 'antonio', 'manuel', 'francisco', 'juan', 'david', 'jose antonio', 'javier',
            'daniel', 'jose manuel', 'francisco javier', 'jesus', 'miguel', 'alejandro', 'carlos',
            'miguel angel', 'rafael', 'jose luis', 'pablo', 'angel', 'pedro', 'ramon', 'jorge',
            'luis', 'alberto', 'diego', 'adrian', 'hugo', 'alvaro', 'ivan', 'marcos', 'ruben',
            'sergio', 'fernando', 'santiago', 'raul', 'jordi', 'joaquin', 'vicente', 'andres',
            'oscar', 'tomas', 'agustin', 'enrique', 'mario', 'jaime', 'roberto', 'julio',
            'emilio', 'victor', 'gonzalo', 'samuel', 'ignacio', 'felix', 'salvador', 'sebastian',
            'gregorio', 'cesar', 'alfredo', 'domingo', 'isidro', 'ricardo', 'felipe', 'cristobal',
            'eduardo', 'mateo', 'sebastian', 'santiago', 'matias', 'nicolas', 'lucas', 'emiliano',
            'joaquin', 'leonardo', 'rodrigo', 'gustavo', 'hector', 'arturo', 'armando', 'ricardo'
        }

        if first_name in female_names:
            return 'f'
        if first_name in male_names:
            return 'm'

        if first_name.endswith('a'):
            if first_name in ('luca', 'borja', 'joshua', 'misha'):
                return 'm'
            return 'f'

        if first_name.endswith('o'):
            return 'm'

        if first_name.endswith(('el', 'er', 'ur', 'us', 'rt', 'or', 'on', 'an', 'ul', 'as', 'ed')):
            if first_name in ('isabel', 'raquel', 'belen', 'rut', 'ruth'):
                return 'f'
            return 'm'

        return 'o'

    def _map_partner_gender(self, partner):
        """Helper to map res.partner gender values or guess it from name/title."""
        if not partner:
            return 'o'
        
        # 1. Try to read explicit gender from res.partner fields
        gender_val = getattr(partner, 'gender', False)
        if not gender_val and hasattr(partner, 'gender_type'):
            gender_val = getattr(partner, 'gender_type', False)

        if gender_val in ('m', 'male', 'Male', 'Masculino'):
            return 'm'
        if gender_val in ('f', 'female', 'Female', 'Femenino'):
            return 'f'
        
        # 2. If gender is not set or is 'o'/'other', guess intelligently
        guessed = self._guess_gender(partner.name, partner.title.name if partner.title else None)
        if guessed in ('m', 'f'):
            _logger.info("IRG Gender Fix: Guessed gender for partner '%s' is '%s'", partner.name, guessed)
            return guessed

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
                    _logger.info("IRG Gender Fix: Mapping empty/default student gender to partner's gender: %s -> %s", partner.name, mapped_gender)
                    vals['gender'] = mapped_gender
                else:
                    vals['gender'] = 'o'

            # Fallback if still not set (gender is required)
            if not vals.get('gender'):
                vals['gender'] = 'o'
        return super(OpStudent, self).create(vals_list)

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
                _logger.info("IRG Gender Fix: Mapping student gender on partner change: %s -> %s", partner.name, mapped_gender)
                vals['gender'] = mapped_gender

        return super(OpStudent, self).write(vals)
