import datetime

from odoo import models


class OpCourse(models.Model):
    _inherit = 'op.course'

    def get_subjects_visible_for_batch(self, batch):
        """Devuelve las asignaturas del curso visibles para el alumno según su lote.

        Combina dos fuentes de verdad:
        - Si visible_all_course_batches=True  → siempre aparece (independientemente del lote)
        - Si visible_all_course_batches=False → usa el sistema clásico de subject_to_batch_ids
          con validación de fechas (igual que irg_subject_fix), respetando la limitación
          por lote existente.

        :param batch: registro de op.batch del alumno (o False si no tiene lote activo)
        :return: recordset de op.subject
        """
        self.ensure_one()
        today = datetime.date.today()

        # Obtener las asignaturas del lote con fechas vigentes (lógica irg_subject_fix)
        batch_date_subjects = self.env['op.subject']
        if batch:
            valid_lines = batch.subject_to_batch_ids.filtered(
                lambda l: l.date_from and l.date_to
                and l.date_from <= today and l.date_to >= today
            )
            batch_date_subjects = valid_lines.mapped('subject_id')

        result = self.env['op.subject']
        for subject in self.subject_ids:
            if subject.visible_all_course_batches:
                # Marcada como visible para todo el curso → siempre aparece
                result |= subject
            elif not batch:
                # Sin lote: comportamiento igual al fallback de irg_subject_fix
                result |= subject
            elif subject in batch_date_subjects:
                # No es de visibilidad global, pero sí está en el lote con fecha vigente
                result |= subject

        return result
