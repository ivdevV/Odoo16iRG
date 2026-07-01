# -*- coding: utf-8 -*-
from odoo import models

class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    def unlink(self):
        for rec in self:
            if rec.gradebook_result_ids:
                rec.gradebook_result_ids.unlink()
        return super(AppGradebookSubject, self).unlink()
