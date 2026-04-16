from odoo import api, fields, models
from odoo.tools.translate import _


class OpSubject(models.Model):
    _inherit = 'op.subject'

    visible_all_course_batches = fields.Boolean(
        string=_('Visible para todos los lotes del curso'),
        default=True,
        help=_(
            'Si está activado, la asignatura es visible en el portal eLearning para todos '
            'los lotes de los cursos a los que pertenece.\n'
            'Si se desactiva, solo será visible para los lotes seleccionados manualmente '
            'en el campo "Lotes con acceso".'
        ),
    )

    batch_visibility_ids = fields.Many2many(
        comodel_name='op.batch',
        relation='op_subject_batch_visibility_rel',
        column1='subject_id',
        column2='batch_id',
        string=_('Lotes con acceso'),
        help=_(
            'Lotes específicos que pueden acceder a esta asignatura en el portal eLearning. '
            'Solo se tiene en cuenta cuando "Visible para todos los lotes del curso" '
            'está desactivado.'
        ),
    )

    effective_batch_ids = fields.Many2many(
        comodel_name='op.batch',
        string=_('Lotes con acceso efectivo'),
        compute='_compute_effective_batch_ids',
        help=_(
            'Lotes que realmente tienen acceso a esta asignatura según la configuración '
            'de visibilidad. Campo de solo lectura para referencia.'
        ),
    )

    @api.depends('visible_all_course_batches', 'batch_visibility_ids', 'course_ids')
    def _compute_effective_batch_ids(self):
        Batch = self.env['op.batch'].sudo()
        for subject in self:
            if subject.visible_all_course_batches:
                course_ids = subject.course_ids.ids
                if course_ids:
                    subject.effective_batch_ids = Batch.search(
                        [('course_id', 'in', course_ids)]
                    )
                else:
                    subject.effective_batch_ids = Batch.browse()
            else:
                subject.effective_batch_ids = subject.batch_visibility_ids

    def is_visible_for_batch(self, batch):
        """Devuelve True si la asignatura es accesible para el lote dado.

        Este método es la fuente de verdad para la restricción de visibilidad
        en el portal eLearning. Se usa desde el controlador del canal de slides.

        :param batch: registro de op.batch (single record)
        :return: bool
        """
        self.ensure_one()
        if not batch:
            return True
        if self.visible_all_course_batches:
            # Visible para cualquier lote cuyo curso esté en los cursos de la asignatura
            return batch.course_id in self.course_ids
        return batch in self.batch_visibility_ids
