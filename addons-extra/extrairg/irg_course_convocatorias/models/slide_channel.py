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
    irg_homeclass_slide_ids = fields.One2many(
        'slide.slide',
        'channel_id',
        string='Contenido HomeClass editable',
        domain=['|', ('irg_content_modality', '=', False), ('irg_content_modality', '=', 'homeclass')],
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
        courses |= self.slide_ids.mapped('allowed_batch_ids.course_id')
        if 'irg_native_section_ids' in self._fields:
            courses |= self.irg_native_section_ids.mapped('allowed_batch_ids.course_id')
        return courses

    def _irg_batch_matches_modality(self, batch, modality_code):
        modality_tokens = self._irg_get_batch_modality_tokens(batch)
        if modality_code == 'homeclass':
            if self._irg_has_online_token(modality_tokens):
                return False
            return self._irg_has_homeclass_token(modality_tokens) or self._irg_batch_has_live_class_link(batch)
        if modality_code == 'online':
            return self._irg_has_online_token(modality_tokens)
        return False

    def _irg_get_batch_modality_tokens(self, batch):
        token_values = []
        modality = batch.modality_id
        if modality:
            for field_name in ('name', 'code', 'new_code', 'analytic_code'):
                if field_name in modality._fields:
                    token_values.append(modality[field_name])
        if 'code' in batch._fields:
            token_values.append(batch.code)
        return [
            self._irg_normalize_modality_token(token_value)
            for token_value in token_values
            if token_value
        ]

    def _irg_normalize_modality_token(self, value):
        return (value or '').strip().lower().replace('-', '').replace('_', '').replace(' ', '')

    def _irg_has_homeclass_token(self, tokens):
        homeclass_tokens = ('homeclass', 'home', 'hc', 'hcl', 'classroom')
        return any(homeclass_token in token for token in tokens for homeclass_token in homeclass_tokens)

    def _irg_has_online_token(self, tokens):
        return any(
            ('online' in token or 'onl' in token)
            and 'monl' not in token
            for token in tokens
        )

    def _irg_batch_has_live_class_link(self, batch):
        return 'teams_link' in batch._fields and bool(batch.teams_link)

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
        """Bootstrap 1:1 del contenido HomeClass al tab Online.

        Crea registros independientes (sin enlace con los originales) usando
        ``create()`` directo en lugar de ``slide.slide.copy()`` para evitar
        side effects de ``website_slides`` y de los hooks de
        ``irg_elearning_editable_sections``. Trabaja en dos pases: primero
        crea los registros con sus datos base, luego remapea las referencias
        jerárquicas (``category_id``, ``parent_slide_id``, ``irg_section_id``).
        Las copias se añaden al final del listado Online y dejan
        ``allowed_batch_ids`` vacío para que el equipo académico los asigne
        manualmente a lotes Online.
        """
        self.ensure_one()
        homeclass_slides = self.slide_ids.filtered(self._irg_is_homeclass_content)
        ordered_slides = homeclass_slides.sorted(lambda slide: (slide.sequence, slide.id))
        if not ordered_slides:
            return self._irg_bootstrap_notification(0)

        clone_env = self.env(context=dict(self.env.context, irg_skip_parent_propagation=True))
        section_map = self._irg_bootstrap_clone_irg_sections(clone_env)
        sequence_offset = self._irg_bootstrap_base_sequence()

        slide_model = clone_env['slide.slide']
        slide_map = {}
        copied_slides = slide_model

        # Pase 1: crear categorías primero y luego contenidos, sin remapeo (queda en pase 2).
        ordered_categories = ordered_slides.filtered(lambda source: source.is_category)
        ordered_contents = ordered_slides.filtered(lambda source: not source.is_category)
        creation_order = list(ordered_categories) + list(ordered_contents)

        for index, source in enumerate(creation_order):
            vals = self._irg_bootstrap_prepare_slide_values(source)
            vals['sequence'] = sequence_offset + (index + 1) * 10
            copy = slide_model.create(vals)
            # Defensa post-create: website_slides aplica defaults de contenido
            # incluso para secciones; reafirmamos los marcadores estructurales.
            if source.is_category and (
                not copy.is_category or copy.slide_category != vals.get('slide_category')
            ):
                copy.write({
                    'is_category': True,
                    'slide_category': vals.get('slide_category'),
                })
            slide_map[source.id] = copy
            copied_slides |= copy

        # Pase 2: remapear referencias jerárquicas con el mapa ya completo.
        for source, copy in ((src, slide_map[src.id]) for src in creation_order):
            updates = self._irg_bootstrap_remap_values(source, slide_map, section_map)
            if updates:
                copy.write(updates)

        # Pase 3: replicar quizzes (preguntas + respuestas) si aplica.
        self._irg_bootstrap_clone_quizzes(creation_order, slide_map, clone_env)

        return self._irg_bootstrap_notification(len(copied_slides))

    def _irg_bootstrap_notification(self, count):
        if not count:
            message = _('No hay contenido HomeClass que copiar.')
        else:
            message = _(
                '%d elemento(s) copiado(s) a Online. Puedes editarlos de forma independiente.'
            ) % count
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bootstrap Online'),
                'message': message,
                'type': 'success' if count else 'warning',
                'sticky': False,
            },
        }

    def _irg_bootstrap_base_sequence(self):
        self.ensure_one()
        existing_online_sequences = self.slide_ids.filtered(
            lambda slide: slide.irg_content_modality == 'online'
        ).mapped('sequence')
        return max(existing_online_sequences or [0])

    def _irg_bootstrap_clone_irg_sections(self, clone_env):
        """Clona todas las secciones iRG del canal (no sólo las referenciadas)."""
        self.ensure_one()
        section_map = {}
        section_model = clone_env.get('irg.slide.section')
        if section_model is None:
            return section_map
        if 'channel_id' not in section_model._fields:
            return section_map

        sections = section_model.search([('channel_id', '=', self.id)], order='sequence, id')
        for section in sections:
            vals = {
                'name': section.name,
                'sequence': section.sequence,
                'channel_id': self.id,
            }
            if 'active' in section._fields:
                vals['active'] = section.active
            if 'convocatoria_id' in section._fields:
                vals['convocatoria_id'] = False
            section_map[section.id] = section_model.create(vals)
        return section_map

    def _irg_bootstrap_slide_clone_fields(self):
        """Whitelist de campos seguros a copiar entre slides HomeClass y Online.

        Cada campo se verifica con ``_fields`` antes de leerse, por lo que la
        lista puede contener campos opcionales de Odoo o de módulos terceros
        sin romper si no están instalados.
        """
        return (
            'name', 'description', 'slide_category', 'is_category',
            'is_published', 'url', 'document_google_url', 'mime_type',
            'datas', 'image_1920', 'html_content', 'video_url',
            'embed_code', 'completion_time', 'access_token',
            'quiz_first_attempt_reward', 'quiz_second_attempt_reward',
            'quiz_third_attempt_reward', 'quiz_fourth_attempt_reward',
            'inherit_limitations_from_parent', 'scheduled_date',
            # website_slides_survey: certificaciones / encuestas vinculadas.
            'survey_id',
        )

    def _irg_bootstrap_prepare_slide_values(self, source):
        """Valores para ``create()`` en el pase 1 (sin referencias remapeables).

        Trata aparte las secciones (``is_category=True``): omite
        ``slide_category`` y demás campos de contenido para no chocar con la
        lógica nativa de ``website_slides`` que asume que una sección no tiene
        categoría de contenido (``document``, ``video``...). De lo contrario
        Odoo cuela el default ``slide_category='document'`` y la copia deja
        de comportarse como sección.
        """
        self.ensure_one()
        is_section = bool(source._fields.get('is_category') and source.is_category)
        # Campos que sólo aplican a contenidos reales, nunca a una sección.
        content_only_fields = {
            'slide_category', 'url', 'document_google_url', 'mime_type',
            'datas', 'html_content', 'video_url', 'embed_code',
            'completion_time', 'survey_id',
            'quiz_first_attempt_reward', 'quiz_second_attempt_reward',
            'quiz_third_attempt_reward', 'quiz_fourth_attempt_reward',
        }
        vals = {
            'channel_id': self.id,
            'irg_content_modality': 'online',
        }
        for field_name in self._irg_bootstrap_slide_clone_fields():
            if field_name == 'access_token':
                # access_token se regenera; no copiar para evitar colisiones.
                continue
            if field_name not in source._fields:
                continue
            if is_section and field_name in content_only_fields:
                continue
            field = source._fields[field_name]
            value = source[field_name]
            if field.type == 'many2one':
                vals[field_name] = value.id if value else False
            elif field.type in ('many2many', 'one2many'):
                # one2many no debería estar en la whitelist; many2many como replace.
                vals[field_name] = [(6, 0, value.ids)]
            else:
                vals[field_name] = value
        if is_section:
            # Forzar marcadores de sección por si la whitelist no los incluye.
            vals['is_category'] = True
            # Las secciones creadas manualmente por la vista usan article como
            # categoría técnica. Si se omite, website_slides usa document por
            # defecto y la sección aparece en Online como "Documento".
            vals['slide_category'] = 'article'
        if 'tag_ids' in source._fields:
            vals['tag_ids'] = [(6, 0, source.tag_ids.ids)]
        # allowed_batch_ids se vacía deliberadamente en bootstrap.
        if 'allowed_batch_ids' in source._fields:
            vals['allowed_batch_ids'] = [(5,)]
        return vals

    def _irg_bootstrap_remap_values(self, source, slide_map, section_map):
        """Devuelve las referencias jerárquicas remapeadas para el pase 2."""
        updates = {}
        if 'category_id' in source._fields:
            target = slide_map.get(source.category_id.id) if source.category_id else False
            updates['category_id'] = target.id if target else False
        if 'parent_slide_id' in source._fields:
            target = slide_map.get(source.parent_slide_id.id) if source.parent_slide_id else False
            updates['parent_slide_id'] = target.id if target else False
        if 'irg_section_id' in source._fields:
            target = section_map.get(source.irg_section_id.id) if source.irg_section_id else False
            updates['irg_section_id'] = target.id if target else False
        return updates

    def _irg_bootstrap_clone_quizzes(self, sources, slide_map, clone_env):
        """Replica ``slide.question`` y ``slide.answer`` para cada slide copiado."""
        question_model = clone_env.get('slide.question')
        if question_model is None:
            return
        answer_model = clone_env.get('slide.answer')
        for source in sources:
            if 'question_ids' not in source._fields or not source.question_ids:
                continue
            copy = slide_map.get(source.id)
            if not copy:
                continue
            for question in source.question_ids:
                q_vals = {'slide_id': copy.id}
                for field_name in ('sequence', 'question'):
                    if field_name in question._fields:
                        q_vals[field_name] = question[field_name]
                new_question = question_model.create(q_vals)
                if answer_model is None or 'answer_ids' not in question._fields:
                    continue
                for answer in question.answer_ids:
                    a_vals = {'question_id': new_question.id}
                    for field_name in ('sequence', 'text_value', 'is_correct', 'comment'):
                        if field_name in answer._fields:
                            a_vals[field_name] = answer[field_name]
                    answer_model.create(a_vals)

    def _irg_is_online_variant(self, variant):
        for line in variant.attribute_line_ids:
            attribute_name = (line.attribute_id.name or '').strip().lower()
            values = [value.name.strip().lower() for value in line.value_ids]
            if attribute_name == 'modalidad' and any('online' in value and 'convenio' not in value for value in values):
                return True
        return False
