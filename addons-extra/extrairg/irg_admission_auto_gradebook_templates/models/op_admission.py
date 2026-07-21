# -*- coding: utf-8 -*-
from odoo import models


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def enroll_student(self):
        super().enroll_student()
        # Libretas creadas por irg_admission_auto_gradebook ya reciben plantilla
        # en app.gradebook.student.create; esto cubre el caso en que la libreta
        # existiera vacía antes del enroll o se creara por otro camino previo.
        gradebooks = self.env['app.gradebook.student'].sudo().search([
            ('admission_id', 'in', self.ids),
            ('gradebook_id', '=', False),
        ])
        gradebooks._irg_assign_canonical_gradebook_template()
