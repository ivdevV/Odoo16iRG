# -*- coding: utf-8 -*-

from odoo import models


class PortalMenu(models.Model):
    _inherit = 'openeducat.portal.menu'

    def irg_is_practice_menu(self):
        self.ensure_one()
        name = (self.name or '').lower()
        link = (self.link or '').lower()
        return 'practic' in name or 'practice_request' in link
