from odoo import _, api, fields, models


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
    irg_online_content_ids = fields.Many2many(
        'slide.slide',
        compute='_compute_irg_course_convocatoria_data',
        string='Contenido Online',
    )
    irg_online_slide_ids = fields.One2many(
        'slide.slide',
        'channel_id',
        string='Contenido Online editable',
        domain=[('irg_content_modality', '=', 'online')],
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
        'slide_ids',
        'slide_ids.allowed_batch_ids',
        'slide_ids.slide_category',
        'slide_ids.is_category',
        'slide_ids.irg_content_modality',
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
                lambda section: channel._irg_is_homeclass_content(section)
                and bool(section.allowed_batch_ids & homeclass_batches)
            )
            online_content = channel.slide_ids.filtered(
                lambda slide: slide.irg_content_modality == 'online'
            )
            online_sections = online_content.filtered(
                lambda slide: slide.is_category
            )

            channel.irg_related_course_ids = related_courses or course_model.browse()
            channel.irg_related_modality_ids = related_modalities or modality_model.browse()
            channel.irg_homeclass_batch_ids = homeclass_batches
            channel.irg_online_batch_ids = online_batches
            channel.irg_homeclass_section_ids = homeclass_sections
            channel.irg_online_content_ids = online_content
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

    def _irg_slide_matches_batches(self, slide, batches):
        if not slide.allowed_batch_ids:
            return False
        return bool(slide.allowed_batch_ids & batches)

    def _irg_is_homeclass_content(self, slide):
        return slide.irg_content_modality in (False, 'homeclass')

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

    def action_copy_homeclass_to_online(self):
        """Copia el contenido de HomeClass al tab Online como registros independientes."""
        self.ensure_one()
        homeclass_slides = self.slide_ids.filtered(self._irg_is_homeclass_content)
        ordered_slides = homeclass_slides.sorted(lambda slide: (slide.sequence, slide.id))
        sequence_map = self._irg_get_online_copy_sequence_map(ordered_slides)
        section_map = self._irg_copy_irg_sections_for_online(homeclass_slides)
        slide_map = {}
        copied_slides = self.env['slide.slide']

        for slide in ordered_slides.filtered(lambda source: source.is_category):
            copied_slide = slide.copy(
                self._irg_prepare_online_slide_copy_values(slide, slide_map, section_map, sequence_map)
            )
            slide_map[slide.id] = copied_slide
            copied_slides |= copied_slide

        for slide in ordered_slides.filtered(lambda source: not source.is_category):
            copied_slide = slide.copy(
                self._irg_prepare_online_slide_copy_values(slide, slide_map, section_map, sequence_map)
            )
            slide_map[slide.id] = copied_slide
            copied_slides |= copied_slide

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Contenido copiado'),
                'message': _('%d elemento(s) copiado(s) a Online. Puedes editarlos de forma independiente.') % len(copied_slides),
                'type': 'success',
                'sticky': False,
            },
        }

    def _irg_get_online_copy_sequence_map(self, ordered_slides):
        self.ensure_one()
        max_sequence = max(self.slide_ids.filtered(
            lambda slide: slide.irg_content_modality == 'online'
        ).mapped('sequence') or [0])
        return {
            slide.id: max_sequence + ((index + 1) * 10)
            for index, slide in enumerate(ordered_slides)
        }

    def _irg_copy_irg_sections_for_online(self, slides):
        self.ensure_one()
        section_map = {}
        if 'irg_section_id' not in self.env['slide.slide']._fields:
            return section_map

        sections = slides.mapped('irg_section_id').filtered(
            lambda section: section.channel_id == self
        ).sorted(lambda section: (section.sequence, section.id))

        for section in sections:
            section_map[section.id] = section.copy({
                'channel_id': self.id,
                'convocatoria_id': False,
            })
        return section_map

    def _irg_prepare_online_slide_copy_values(self, slide, slide_map, section_map, sequence_map):
        self.ensure_one()
        values = {
            'name': slide.name,
            'sequence': sequence_map[slide.id],
            'is_category': slide.is_category,
            'slide_category': slide.slide_category,
            'irg_content_modality': 'online',
            'is_published': slide.is_published,
        }

        if 'category_id' in slide._fields:
            copied_category = slide_map.get(slide.category_id.id) if slide.category_id else False
            values['category_id'] = copied_category.id if copied_category else False

        if 'parent_slide_id' in slide._fields:
            copied_parent = slide_map.get(slide.parent_slide_id.id) if slide.parent_slide_id else False
            values['parent_slide_id'] = copied_parent.id if copied_parent else False

        if 'irg_section_id' in slide._fields:
            copied_section = section_map.get(slide.irg_section_id.id) if slide.irg_section_id else False
            values['irg_section_id'] = copied_section.id if copied_section else False

        return values

    def _irg_is_online_variant(self, variant):
        for line in variant.attribute_line_ids:
            attribute_name = (line.attribute_id.name or '').strip().lower()
            values = [value.name.strip().lower() for value in line.value_ids]
            if attribute_name == 'modalidad' and any('online' in value and 'convenio' not in value for value in values):
                return True
        return False
