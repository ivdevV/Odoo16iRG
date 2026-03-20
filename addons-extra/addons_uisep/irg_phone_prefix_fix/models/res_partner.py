# -*- coding: utf-8 -*-
# IRG: Override phone formatting to preserve the Mexican "1" trunk prefix (+521...).
#
# Root cause:
#   Google's phonenumbers library (libphonenumber) treats +521XXXXXXXXXX as the same
#   number as +52XXXXXXXXXX. The "1" was historically a long-distance prefix inside
#   Mexico, deprecated in 2020 by IFT. The library considers both representations
#   equivalent and always normalises to the shorter form (E.164: +52XXXXXXXXXX).
#
#   Odoo's _phone_format() calls phone_validation.phone_format() on every onchange
#   of phone/mobile/country_id, so any number entered as "+52 1 55 1234 5678" is
#   silently saved as "+52 55 1234 5678". No error is raised; the digit just vanishes.
#
# Approach:
#   Override _phone_format() in res.partner.
#   If the user typed the +521 prefix, detect it from the raw input and restore it
#   after the library normalises the number.
#
# About the "*****" asterisk problem:
#   fields.Char never renders asterisks on its own. Asterisks appear ONLY when:
#     a) A view XML has  password="True"  on the field tag, OR
#     b) The field definition carries  groups="..."  restricting read access, OR
#     c) An enterprise Privacy / Anonymization module hashes the value at DB level.
#   Adding  widget="char"  in the view XML forces Odoo to render the raw stored
#   string without any formatting or masking.
#   This module also ships that view override (see views/res_partner_views.xml).

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _irg_strip_phone(number):
        """Return only digits from a phone string (drop +, spaces, dashes, parens)."""
        return ''.join(c for c in (number or '') if c.isdigit())

    @staticmethod
    def _irg_user_typed_mx1(number):
        """
        Return True if the user explicitly typed the transitional '1' after +52.

        Accepted: digits starting with 521 and total 13 digits (52+1+10subscriber).
        We do NOT trigger on bare '1XXXXXXXXXX' without the 52 prefix, because a
        Mexican contact might enter just the 10-digit local number.
        """
        digits = ''.join(c for c in (number or '') if c.isdigit())
        return digits.startswith('521') and len(digits) == 13  # 52 + 1 + 10 digits

    # ------------------------------------------------------------------
    # Core override
    # ------------------------------------------------------------------

    def _phone_format(self, number, country=None, company=None, force_format='E164'):
        """
        Preserve the Mexican '+52 1' trunk prefix if the user typed it.

        Strategy:
          1. Remember whether the raw input had the trunk '1'.
          2. Let Odoo/phonenumbers normalise as usual.
          3. If the result starts with +52 (but not +521) and the original had the
             '1', inject it back before returning.
        """
        if not number or not isinstance(number, str):
            return super()._phone_format(
                number, country=country, company=company, force_format=force_format
            )

        user_typed_one = self._irg_user_typed_mx1(number)

        result = super()._phone_format(
            number, country=country, company=company, force_format=force_format
        )

        if not result or not user_typed_one:
            return result

        result_digits = self._irg_strip_phone(result)

        # The library dropped the '1': result is +52XXXXXXXXXX (12 digits total)
        if result_digits.startswith('52') and not result_digits.startswith('521'):
            suffix_digits = result_digits[2:]  # 10-digit subscriber number
            if force_format == 'E164':
                return '+521' + suffix_digits
            # INTERNATIONAL / default: "+52 1 XX XXXX XXXX"
            if result.startswith('+52 '):
                return '+52 1 ' + result[4:]
            return '+52 1 ' + suffix_digits

        return result

    # ------------------------------------------------------------------
    # Guard the live-form onchanges so the UI shows the preserved number
    # ------------------------------------------------------------------

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self._phone_format(self.phone, force_format='INTERNATIONAL')

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self._phone_format(self.mobile, force_format='INTERNATIONAL')
