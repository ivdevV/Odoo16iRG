# -*- coding: utf-8 -*-
import logging
import unicodedata

from odoo import fields, models

_logger = logging.getLogger(__name__)

_MALE_VALUES = frozenset({'m', 'male', 'Male', 'Masculino'})
_FEMALE_VALUES = frozenset({'f', 'female', 'Female', 'Femenino'})
_OTHER_VALUES = frozenset({'o', 'other', 'not-sure', 'Other', 'Otro'})

_FEMALE_TITLES = ('sra', 'mrs', 'ms', 'dna', 'dona', 'dra', 'senora')
_MALE_TITLES = ('sr', 'mr', 'don', 'senor', 'dr')

_FEMALE_NAMES = frozenset({
    'maria', 'ana', 'carmen', 'josefa', 'isabel', 'marta', 'sara', 'ana maria',
    'maria carmen', 'laura', 'cristina', 'pilar', 'antonia', 'dolores', 'teresa',
    'francisca', 'elena', 'patricia', 'monica', 'alicia', 'rosa', 'beatriz',
    'julia', 'silvia', 'raquel', 'irene', 'clara', 'lorena', 'vanesa', 'angela',
    'mercedes', 'rocio', 'gemma', 'olga', 'eva', 'paula', 'alba', 'noelia',
    'sofia', 'miriam', 'estela', 'mar', 'nieves', 'concepcion', 'juana', 'luisa',
    'manuela', 'margarita', 'gloria', 'amparo', 'lourdes', 'inmaculada',
    'virginia', 'susana', 'yolanda', 'esther', 'rebeca', 'nuria', 'loreto',
    'begona', 'arancha', 'nerea', 'itziar', 'amaia', 'ainhoa', 'leire', 'maite',
    'estefania', 'andrea', 'belen', 'ines', 'montserrat', 'lucia', 'gabriela',
    'valeria', 'daniela', 'camila', 'mariana', 'regina', 'ximena', 'jimena',
    'renata', 'victoria', 'sandra', 'paola', 'claudia', 'diana', 'veronica',
    'adriana', 'leticia',
})

_MALE_NAMES = frozenset({
    'jose', 'antonio', 'manuel', 'francisco', 'juan', 'david', 'jose antonio',
    'javier', 'daniel', 'jose manuel', 'francisco javier', 'jesus', 'miguel',
    'alejandro', 'carlos', 'miguel angel', 'rafael', 'jose luis', 'pablo',
    'angel', 'pedro', 'ramon', 'jorge', 'luis', 'alberto', 'diego', 'adrian',
    'hugo', 'alvaro', 'ivan', 'marcos', 'ruben', 'sergio', 'fernando',
    'santiago', 'raul', 'jordi', 'joaquin', 'vicente', 'andres', 'oscar',
    'tomas', 'agustin', 'enrique', 'mario', 'jaime', 'roberto', 'julio',
    'emilio', 'victor', 'gonzalo', 'samuel', 'ignacio', 'felix', 'salvador',
    'sebastian', 'gregorio', 'cesar', 'alfredo', 'domingo', 'isidro', 'ricardo',
    'felipe', 'cristobal', 'eduardo', 'mateo', 'matias', 'nicolas', 'lucas',
    'emiliano', 'leonardo', 'rodrigo', 'gustavo', 'hector', 'arturo', 'armando',
})


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Moodle connector marks username required=True on all partners; that blocks
    # editing gender (and general contact data) when no Moodle user exists yet.
    username = fields.Char(string='Username', required=False)

    def _irg_clean_string(self, value):
        if not value:
            return ''
        value = unicodedata.normalize('NFKD', value).encode('ASCII', 'ignore').decode('ASCII')
        return value.strip().lower()

    def _irg_normalize_gender(self, gender_val):
        if gender_val in _MALE_VALUES:
            return 'm'
        if gender_val in _FEMALE_VALUES:
            return 'f'
        if gender_val in _OTHER_VALUES:
            return 'o'
        return False

    def _irg_guess_gender(self):
        """Guess gender from title and/or first name (same heuristics as gender_fix)."""
        self.ensure_one()
        title_name = self.title.name if self.title else None
        if title_name:
            title_clean = self._irg_clean_string(title_name)
            for female_title in _FEMALE_TITLES:
                if female_title in title_clean:
                    return 'f'
            for male_title in _MALE_TITLES:
                if male_title in title_clean:
                    return 'm'

        name = self.name or ''
        parts = name.split()
        if not parts:
            return 'o'
        first_name = self._irg_clean_string(parts[0])

        if first_name in _FEMALE_NAMES:
            return 'f'
        if first_name in _MALE_NAMES:
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

    def _irg_resolve_gender(self, order_gender=False, write_back=True):
        """Resolve gender: order → partner → heuristic → 'o'. Optionally persist guesses."""
        self.ensure_one()
        for candidate in (order_gender, self.gender):
            normalized = self._irg_normalize_gender(candidate)
            if normalized in ('m', 'f'):
                return normalized

        guessed = self._irg_guess_gender()
        if guessed in ('m', 'f'):
            partner_normalized = self._irg_normalize_gender(self.gender)
            if write_back and partner_normalized not in ('m', 'f'):
                _logger.info(
                    "IRG Partner Gender: writing guessed gender '%s' on partner '%s'",
                    guessed, self.name,
                )
                self.with_context(skip_moodle_sync=True).write({'gender': guessed})
            return guessed
        return 'o'
