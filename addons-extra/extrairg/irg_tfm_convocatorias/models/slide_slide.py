from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_tfm_convocation_ids = fields.Many2many(
        'irg.tfm.convocatoria',
        'slide_slide_tfm_convocation_rel',
        'slide_id',
        'convocation_id',
        string='Convocatorias TFM',
        copy=True,
        help=(
            'Solo las categorías pueden configurar convocatorias. El contenido '
            'hereda la restricción efectiva de su categoría o padre; vacío '
            'significa contenido común dentro del canal TFM.'
        ),
    )

    @api.constrains('irg_tfm_convocation_ids', 'is_category')
    def _check_tfm_convocations_only_on_categories(self):
        for slide in self:
            if slide.irg_tfm_convocation_ids and not slide.is_category:
                raise ValidationError(_(
                    'TFM convocations can only be configured on eLearning categories.'
                ))

    def _irg_effective_tfm_convocation_ids(self):
        """Return the category-level TFM restriction inherited by this slide."""
        self.ensure_one()
        slide = self.sudo()
        if slide.is_category and slide.irg_tfm_convocation_ids:
            return slide.irg_tfm_convocation_ids
        category = slide.category_id.sudo()
        if category and category.irg_tfm_convocation_ids:
            return category.irg_tfm_convocation_ids
        parent = slide.parent_slide_id.sudo()
        if parent and parent.irg_tfm_convocation_ids:
            return parent.irg_tfm_convocation_ids
        return self.env['irg.tfm.convocatoria']

    def irg_has_tfm_requirement(self):
        self.ensure_one()
        return bool(self._irg_effective_tfm_convocation_ids())

    def _irg_tfm_current_convocation_for_user(self, user, channel=None):
        """Resolve one portal enrollment and its one active TFM record.

        This deliberately does not inspect slide memberships. A membership is
        useful to the generic eLearning stack, but it is not evidence that the
        portal user owns the current TFM enrollment.
        """
        self.ensure_one()
        user = user or self.env.user
        if not user or user._is_public() or user.has_group('base.group_user'):
            return self.env['irg.tfm.convocatoria']

        channel = (channel or self.sudo().channel_id).sudo()
        if not channel:
            return self.env['irg.tfm.convocatoria']

        Student = self.env['op.student'].sudo().with_context(active_test=False)
        students = Student.search([('user_id', '=', user.id)], limit=2)
        if len(students) != 1 or not students.active:
            return self.env['irg.tfm.convocatoria']

        Enrollment = self.env['op.student.course'].sudo().with_context(active_test=False)
        enrollments = Enrollment.search([
            ('student_id', '=', students.id),
            ('student_id.user_id', '=', user.id),
            ('course_id.irg_tfm_channel_id', '=', channel.id),
        ], limit=2)
        if len(enrollments) != 1:
            return self.env['irg.tfm.convocatoria']

        theses = self.env['tesis.model'].sudo().with_context(active_test=False).search([
            ('course_id', '=', enrollments.id),
            ('course_id.student_id', '=', students.id),
            ('course_id.student_id.user_id', '=', user.id),
            ('course_id.course_id.irg_tfm_channel_id', '=', channel.id),
            ('irg_tfm_activated_at', '!=', False),
        ], limit=2)
        if len(theses) != 1 or not theses.irg_tfm_convocation_id.active:
            return self.env['irg.tfm.convocatoria']
        return theses.irg_tfm_convocation_id

    def is_user_allowed_by_tfm_convocation(self, user=None):
        """Fail closed for portal users when a category is exclusive."""
        self.ensure_one()
        required = self._irg_effective_tfm_convocation_ids()
        if not required:
            return True

        user = user or self.env.user
        if user and user.has_group('base.group_user'):
            return True
        if not user or user._is_public():
            return False

        current = self._irg_tfm_current_convocation_for_user(user)
        return bool(current and current.id in required.ids)
