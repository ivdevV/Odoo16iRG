from odoo import _, models
from odoo.exceptions import UserError


class OpBatch(models.Model):
    _inherit = 'op.batch'

    def action_irg_reload_subject_to_batch(self):
        self.ensure_one()
        if not self.course_id:
            raise UserError(_(
                'No se pueden recargar asignaturas porque el lote no tiene un curso asignado.'
            ))

        course_subjects = self.course_id.subject_ids
        course_subject_ids = set(course_subjects.ids)
        existing_by_subject = {}
        lines_to_remove = self.env['op.subject.to.batch']

        for line in self.subject_to_batch_ids:
            subject_id = line.subject_id.id
            if (
                not subject_id
                or subject_id not in course_subject_ids
                or subject_id in existing_by_subject
            ):
                lines_to_remove |= line
                continue
            existing_by_subject[subject_id] = line

        removed_count = len(lines_to_remove)
        if lines_to_remove:
            lines_to_remove.unlink()

        created_count = 0
        subject_to_batch_model = self.env['op.subject.to.batch']
        for subject in course_subjects:
            if subject.id in existing_by_subject:
                continue
            subject_to_batch_model.create({
                'batch_id': self.id,
                'subject_id': subject.id,
                'code': subject.code,
            })
            created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Asignaturas recargadas'),
                'message': _(
                    'Sincronizacion completada: %(created)d asignaturas anadidas y '
                    '%(removed)d lineas eliminadas.'
                ) % {
                    'created': created_count,
                    'removed': removed_count,
                },
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                },
            },
        }