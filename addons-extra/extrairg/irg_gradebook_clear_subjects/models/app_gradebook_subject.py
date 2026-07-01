# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError

class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(_("No se puede eliminar una asignatura si la libreta de calificaciones está finalizada."))
            if rec.gradebook_result_ids:
                rec.gradebook_result_ids.unlink()
        return super(AppGradebookSubject, self).unlink()
