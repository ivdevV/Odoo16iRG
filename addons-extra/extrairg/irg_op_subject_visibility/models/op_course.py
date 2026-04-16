from odoo import models


class OpCourse(models.Model):
    _inherit = 'op.course'

    def get_subjects_visible_for_batch(self, batch):
        """Devuelve las asignaturas del curso que son visibles para el lote dado.

        Llamado desde la plantilla QWeb del perfil del alumno para filtrar
        las asignaturas según la configuración de irg_op_subject_visibility.

        :param batch: registro de op.batch (o False)
        :return: recordset de op.subject
        """
        self.ensure_one()
        result = self.env['op.subject']
        for subject in self.subject_ids:
            if subject.is_visible_for_batch(batch):
                result |= subject
        return result
