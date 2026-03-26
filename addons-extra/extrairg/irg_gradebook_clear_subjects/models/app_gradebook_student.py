# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def action_clear_subjects(self):
        """Elimina todas las asignaturas de la libreta.

        Bloquea si alguna asignatura tiene evaluaciones registradas, para
        evitar pérdida de datos accidental.
        """
        self.ensure_one()
        for subject in self.gradebook_subject_ids:
            if subject.gradebook_result_ids:
                raise UserError(
                    _('La asignatura "%s" tiene evaluaciones registradas. '
                      'Debe eliminar primero todas sus evaluaciones antes de '
                      'borrar las asignaturas.')
                    % subject.name
                )
        self.gradebook_subject_ids.unlink()
