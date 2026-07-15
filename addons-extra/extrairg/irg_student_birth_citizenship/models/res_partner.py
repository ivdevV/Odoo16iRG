# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    birth_place = fields.Char(string="Población de nacimiento")
    birth_country_id = fields.Many2one(
        "res.country",
        string="País de nacimiento",
        ondelete="restrict",
    )
    citizenship_country_id = fields.Many2one(
        "res.country",
        string="País de ciudadanía",
        ondelete="restrict",
    )
