from odoo import api, fields, models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    irg_related_course_ids = fields.Many2many(
        'op.course',
        compute='_compute_irg_course_convocatoria_data',
        string='Cursos relacionados',
    )
    irg_related_modality_ids = fields.Many2many(
        'irg.course.modality',
        compute='_compute_irg_course_convocatoria_data',
        string='Modalidades relacionadas',
    )
    irg_homeclass_batch_ids = fields.Many2many(
        'op.batch',
        compute='_compute_irg_course_convocatoria_data',
        string='Convocatorias HomeClass',
    )
    irg_online_batch_ids = fields.Many2many(
        'op.batch',
        compute='_compute_irg_course_convocatoria_data',
        string='Convocatorias Online',
    )
    irg_homeclass_section_ids = fields.Many2many(
        'slide.slide',
        compute='_compute_irg_course_convocatoria_data',
        string='Secciones HomeClass',
    )
    irg_online_section_ids = fields.Many2many(
        'slide.slide',
        compute='_compute_irg_course_convocatoria_data',
        string='Secciones Online',
    )
    irg_online_variant_id = fields.Many2one(
        'product.product',
        compute='_compute_irg_course_convocatoria_data',
        string='Variante Online',
    )
    irg_has_homeclass = fields.Boolean(
        compute='_compute_irg_course_convocatoria_data',
        string='Tiene HomeClass',
    )
    irg_has_online = fields.Boolean(
        compute='_compute_irg_course_convocatoria_data',
        string='Tiene Online',
    )

    @api.depends(
        'op_subject_ids',
        'op_subject_ids.course_id',
        'op_subject_ids.course_id.irg_modality_ids',
        'irg_native_section_ids',
        'irg_native_section_ids.allowed_batch_ids',
    )
    def _compute_irg_course_convocatoria_data(self):
        course_model = self.env['op.course']
        batch_model = self.env['op.batch']
        modality_model = self.env['irg.course.modality']
        product_model = self.env['product.product']

        for channel in self:
            related_courses = channel._irg_get_related_courses()
            related_modalities = related_courses.mapped('irg_modality_ids')
            batches = batch_model.search([('course_id', 'in', related_courses.ids)]) if related_courses else batch_model.browse()

            homeclass_batches = batches.filtered(lambda batch: channel._irg_batch_matches_modality(batch, 'homeclass'))
            online_batches = batches.filtered(lambda batch: channel._irg_batch_matches_modality(batch, 'online'))
            homeclass_sections = channel.irg_native_section_ids.filtered(
                lambda section: bool(section.allowed_batch_ids & homeclass_batches)
            )
            online_sections = channel.irg_native_section_ids.filtered(
                lambda section: bool(section.allowed_batch_ids & online_batches)
            )

            channel.irg_related_course_ids = related_courses or course_model.browse()
            channel.irg_related_modality_ids = related_modalities or modality_model.browse()
            channel.irg_homeclass_batch_ids = homeclass_batches
            channel.irg_online_batch_ids = online_batches
            channel.irg_homeclass_section_ids = homeclass_sections
            channel.irg_online_section_ids = online_sections
            channel.irg_has_homeclass = bool(related_modalities.filtered(lambda modality: modality.code == 'homeclass') or homeclass_batches)
            channel.irg_has_online = bool(related_modalities.filtered(lambda modality: modality.code == 'online') or online_batches)
            channel.irg_online_variant_id = channel._irg_get_online_variant(related_courses) or product_model.browse()

    def _irg_get_related_courses(self):
        self.ensure_one()
        course_model = self.env['op.course']
        courses = self.op_subject_ids.mapped('course_id')
        if self.op_subject_ids:
            courses |= course_model.search([('subject_ids', 'in', self.op_subject_ids.ids)])
        if 'slide_channel_ids' in course_model._fields:
            courses |= course_model.search([('slide_channel_ids', 'in', self.id)])
        return courses

    def _irg_batch_matches_modality(self, batch, modality_code):
        modality_name = (batch.modality_id.name or '').strip().lower()
        batch_code = (batch.code or '').strip().lower()
        if modality_code == 'homeclass':
            return 'homeclass' in modality_name
        if modality_code == 'online':
            return 'online' in modality_name or ('onl' in batch_code and 'monl' not in batch_code)
        return False

    def _irg_get_online_variant(self, courses):
        self.ensure_one()
        for course in courses:
            product = course.product_id if 'product_id' in course._fields else False
            template = product.product_tmpl_id if product else False
            variants = template.product_variant_ids if template else self.env['product.product']
            online_variant = variants.filtered(self._irg_is_online_variant)[:1]
            if online_variant:
                return online_variant
        return self.env['product.product']

    def _irg_is_online_variant(self, variant):
        for line in variant.attribute_line_ids:
            attribute_name = (line.attribute_id.name or '').strip().lower()
            values = [value.name.strip().lower() for value in line.value_ids]
            if attribute_name == 'modalidad' and any('online' in value and 'convenio' not in value for value in values):
                return True
        return False
