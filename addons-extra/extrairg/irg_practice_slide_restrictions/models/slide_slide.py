# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_required_practice_type = fields.Selection(
        selection='_selection_irg_practice_types',
        string='Modalidad de prácticas requerida',
        help='Vacío: visible para todos. Con valor: solo alumnos cuya '
             'matrícula de este curso tenga esa modalidad. Un contenido '
             'hijo dentro de una sección etiquetada queda restringido '
             'aunque su propio campo esté vacío; el flag de heredar '
             'límites solo copia el valor al hijo, no relaja el filtro.',
    )

    @api.model
    def _selection_irg_practice_types(self):
        field = self.env['practice.center.type']._fields.get('type_of_practice')
        if not field:
            return []
        return field._description_selection(self.env)

    def _irg_effective_practice_type(self):
        self.ensure_one()
        slide = self.sudo()
        return (
            slide.irg_required_practice_type
            or slide.category_id.irg_required_practice_type
            or slide.parent_slide_id.irg_required_practice_type
        )

    def irg_has_practice_requirement(self):
        self.ensure_one()
        return bool(self._irg_effective_practice_type())

    def _irg_courses_for_channel(self):
        self.ensure_one()
        channel = self.channel_id.sudo()
        Course = self.env['op.course'].sudo()
        Subject = self.env['op.subject'].sudo()
        courses = Course.browse()
        if not channel:
            return courses
        subjects = (
            channel.op_subject_ids
            if 'op_subject_ids' in channel._fields
            else Subject.browse()
        )
        if subjects:
            if 'course_id' in subjects._fields:
                courses |= subjects.mapped('course_id')
            courses |= Course.search([('subject_ids', 'in', subjects.ids)])
        if 'slide_channel_ids' in Course._fields:
            courses |= Course.search([('slide_channel_ids', 'in', [channel.id])])
        return courses

    def _irg_student_for_user(self, user):
        Student = self.env['op.student'].sudo()
        student = Student.search([('user_id', '=', user.id)], limit=1)
        if not student and user.partner_id:
            student = Student.search(
                [('partner_id', '=', user.partner_id.id)],
                limit=1,
            )
        return student

    def is_user_allowed_by_practice_type(self, user, student=None, courses=None):
        self.ensure_one()
        required = self._irg_effective_practice_type()
        if not required:
            return True
        if not user or user._is_public():
            return False

        if student is None:
            student = self._irg_student_for_user(user)
        if not student:
            return False

        if courses is None:
            courses = self._irg_courses_for_channel()
        enrollments = student.course_detail_ids.filtered(
            lambda rec: rec.course_id in courses
        )
        return any(
            rec.irg_practice_center_type_id.type_of_practice == required
            for rec in enrollments
        )

    @api.onchange('parent_slide_id', 'inherit_limitations_from_parent')
    def _onchange_parent_slide_apply_limitations(self):
        super()._onchange_parent_slide_apply_limitations()
        if self.env.context.get('irg_skip_parent_propagation'):
            return
        for slide in self:
            parent = slide.parent_slide_id
            if (
                parent
                and slide.inherit_limitations_from_parent
                and parent.irg_required_practice_type
                and not slide.irg_required_practice_type
            ):
                slide.irg_required_practice_type = parent.irg_required_practice_type

    def _apply_parent_limitations(self, only_empty=True):
        super()._apply_parent_limitations(only_empty=only_empty)
        if self.env.context.get('irg_skip_parent_propagation'):
            return
        for slide in self.filtered(
            lambda rec: rec.parent_slide_id and rec.inherit_limitations_from_parent
        ):
            parent = slide.parent_slide_id.sudo()
            if parent.irg_required_practice_type and (
                not only_empty or not slide.irg_required_practice_type
            ):
                super(SlideSlide, slide).write({
                    'irg_required_practice_type': parent.irg_required_practice_type,
                })
