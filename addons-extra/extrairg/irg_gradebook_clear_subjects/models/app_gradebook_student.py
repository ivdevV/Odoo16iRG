# -*- coding: utf-8 -*-
from odoo import models, _


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def action_clear_subjects(self):
        """Elimina todas las asignaturas de la libreta, incluidas sus evaluaciones."""
        self.ensure_one()
        # Primero eliminar todas las evaluaciones de cada asignatura
        for subject in self.gradebook_subject_ids:
            if subject.gradebook_result_ids:
                subject.gradebook_result_ids.unlink()
        # Luego eliminar las asignaturas
        self.gradebook_subject_ids.unlink()
