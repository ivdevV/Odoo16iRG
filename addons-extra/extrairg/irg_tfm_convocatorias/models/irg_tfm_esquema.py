import logging

from psycopg2 import IntegrityError

from odoo import api, Command, fields, models, _
from odoo.exceptions import AccessError, ValidationError
from odoo.tools import email_split


_MAX_CHAR_ANSWER = 500
_MAX_TEXT_ANSWER = 20000
_MAX_OPTIONS = 100
_MAX_SELECTED_OPTIONS = 50
_MAX_QUESTIONS = 100
_MAX_TOTAL_TEXT = 100000
_SUPPORTED_TYPES = {'char_box', 'text_box', 'simple_choice', 'multiple_choice'}
_STEP_SELECTION = [
    ('proposal', 'Datos y propuesta'),
    ('approach', 'Planteamiento'),
    ('results', 'Resultados y fuentes'),
]
_STEP_KEYS = tuple(key for key, _label in _STEP_SELECTION)
_PREFILL_KEYS = ('student_name', 'student_email', 'master_name')
_SERVICE_CONTEXT = '_irg_tfm_outline_service'
_VERSION_CONSTRAINT = 'irg_tfm_outline_version_unique'

_logger = logging.getLogger(__name__)


class IrgTfmTemplateError(ValidationError):
    """Internal configuration error that must not be exposed in the portal."""


class IrgTfmEsquema(models.Model):
    _name = 'irg.tfm.esquema'
    _description = 'Esquema TFM versionado'
    _order = 'submitted_at desc, started_at desc, id desc'

    thesis_id = fields.Many2one(
        'tesis.model', required=True, readonly=True, index=True, ondelete='restrict',
    )
    survey_id = fields.Many2one(
        'survey.survey', required=True, readonly=True, ondelete='restrict',
    )
    survey_title = fields.Char(required=True, readonly=True)
    version = fields.Integer(required=True, readonly=True, default=0, index=True)
    state = fields.Selection(
        [('draft', 'Borrador'), ('done', 'Enviado')],
        required=True,
        readonly=True,
        default='draft',
        index=True,
    )
    revision = fields.Integer(required=True, readonly=True, default=0)
    current_step = fields.Selection(
        _STEP_SELECTION, required=True, readonly=True, default='proposal',
    )
    started_by = fields.Many2one(
        'res.users', required=True, readonly=True, ondelete='restrict',
    )
    started_at = fields.Datetime(required=True, readonly=True)
    submitted_at = fields.Datetime(readonly=True)
    question_ids = fields.One2many(
        'irg.tfm.esquema.pregunta', 'outline_id', string='Respuestas', readonly=True,
    )

    _sql_constraints = [
        (
            _VERSION_CONSTRAINT,
            'unique(thesis_id, version)',
            'Ya existe esta versión del Esquema para el expediente.',
        ),
        (
            'irg_tfm_outline_state_consistent',
            "CHECK((state = 'draft' AND version = 0 AND submitted_at IS NULL) "
            "OR (state = 'done' AND version > 0 AND submitted_at IS NOT NULL))",
            'El estado y la versión del Esquema no son coherentes.',
        ),
        (
            'irg_tfm_outline_revision_nonnegative',
            'CHECK(revision >= 0)',
            'La revisión del borrador no puede ser negativa.',
        ),
    ]

    def name_get(self):
        result = []
        for record in self:
            label = _('Esquema — Borrador') if record.state == 'draft' else _(
                'Esquema — Versión %s'
            ) % record.version
            result.append((record.id, label))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get(_SERVICE_CONTEXT):
            raise AccessError(_('TFM outlines can only be created by the protected service.'))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(_SERVICE_CONTEXT):
            raise AccessError(_('TFM outline history is immutable.'))
        if any(record.state == 'done' for record in self):
            raise AccessError(_('TFM outline history is immutable.'))
        allowed = {'revision', 'current_step', 'state', 'version', 'submitted_at'}
        if set(vals) - allowed:
            raise AccessError(_('TFM outline history is immutable.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(_('TFM outline history is immutable.'))

    def copy(self, default=None):
        raise AccessError(_('TFM outline history is immutable.'))

    @api.model
    def _irg_configured_survey(self):
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'irg_tfm_convocatorias.outline_survey_id'
        )
        if raw:
            try:
                survey = self.env['survey.survey'].sudo().browse(int(raw)).exists()
            except (TypeError, ValueError):
                survey = self.env['survey.survey']
        else:
            survey = self.env.ref(
                'irg_tfm_convocatorias.tfm_outline_survey', raise_if_not_found=False,
            )
            if survey:
                survey = survey.sudo()
        if not survey:
            raise IrgTfmTemplateError(_(
                'No está configurada la encuesta de Esquema TFM.'
            ))
        if not survey.irg_tfm_template_only:
            raise IrgTfmTemplateError(_(
                'La encuesta configurada debe estar marcada como plantilla TFM.'
            ))
        return survey

    @api.model
    def _irg_template_snapshot(self, survey):
        items = survey.sudo().question_and_page_ids.sorted(
            key=lambda item: (item.sequence, item.id)
        )
        pages = {}
        questions = []
        current_page = False
        prefill_counts = {key: 0 for key in _PREFILL_KEYS}
        for item in items:
            if item.is_page:
                key = item.irg_tfm_step_key
                if not key or key in pages:
                    raise IrgTfmTemplateError(_(
                        'La encuesta TFM debe tener una única sección para cada paso técnico.'
                    ))
                pages[key] = item
                current_page = item
                continue
            if not current_page or current_page.irg_tfm_step_key not in _STEP_KEYS:
                raise IrgTfmTemplateError(_(
                    'Todas las preguntas TFM deben estar dentro de una sección válida.'
                ))
            if item.question_type not in _SUPPORTED_TYPES:
                raise IrgTfmTemplateError(_(
                    'La pregunta “%s” usa un tipo no compatible con el formulario TFM.'
                ) % item.title)
            options = item.suggested_answer_ids.sorted(
                key=lambda option: (option.sequence, option.id)
            )
            if len(options) > _MAX_OPTIONS:
                raise IrgTfmTemplateError(_(
                    'Una pregunta TFM no puede tener más de %s opciones.'
                ) % _MAX_OPTIONS)
            if item.question_type in ('simple_choice', 'multiple_choice') and not options:
                raise IrgTfmTemplateError(_(
                    'Las preguntas de selección deben tener opciones.'
                ))
            if item.irg_tfm_prefill_source:
                if item.question_type != 'char_box':
                    raise IrgTfmTemplateError(_(
                        'Los campos automáticos de nombre, correo y máster deben '
                        'ser preguntas de texto corto.'
                    ))
                prefill_counts[item.irg_tfm_prefill_source] += 1
            questions.append((current_page, item, options))
        if set(pages) != set(_STEP_KEYS) or len(pages) != len(_STEP_KEYS):
            raise IrgTfmTemplateError(_(
                'La encuesta TFM debe contener los pasos Datos y propuesta, '
                'Planteamiento y Resultados y fuentes.'
            ))
        if len(questions) > _MAX_QUESTIONS:
            raise IrgTfmTemplateError(_(
                'La encuesta TFM no puede superar %s preguntas.'
            ) % _MAX_QUESTIONS)
        if any(count != 1 for count in prefill_counts.values()):
            raise IrgTfmTemplateError(_(
                'La encuesta TFM debe tener exactamente un campo automático de '
                'nombre, correo y máster.'
            ))
        return questions

    @api.model
    def _irg_lock_owned_configuration(self, course_id):
        thesis = self.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=True,
        )
        thesis = self.env['irg.tfm.entrega']._irg_lock_submission_configuration(thesis)
        owned = self.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=True,
        )
        if owned.id != thesis.id:
            raise AccessError(_('El expediente TFM solicitado no está disponible.'))
        if thesis.irg_tfm_convocation_id:
            raise ValidationError(_(
                'El Esquema se ha cerrado porque ya tienes una convocatoria asignada.'
            ))
        return thesis

    @api.model
    def _irg_portal_start(self, course_id):
        thesis = self._irg_lock_owned_configuration(course_id)
        Outline = self.sudo().with_context(**{_SERVICE_CONTEXT: True})
        draft = Outline.search([
            ('thesis_id', '=', thesis.id),
            ('state', '=', 'draft'),
            ('version', '=', 0),
        ], limit=1)
        if draft:
            return draft
        try:
            survey = self._irg_configured_survey()
            snapshot = self._irg_template_snapshot(survey)
        except IrgTfmTemplateError:
            _logger.exception('Invalid TFM outline survey configuration')
            raise ValidationError(_(
                'El cuestionario del Esquema no está disponible temporalmente. '
                'Contacta con el equipo académico.'
            ))
        student = thesis.course_id.student_id
        prefill = {
            'student_name': student.name or '',
            'student_email': student.email or '',
            'master_name': thesis.course_id.course_id.name or '',
        }
        question_commands = []
        for page, question, options in snapshot:
            question_commands.append(Command.create({
                'template_question_id': question.id,
                'sequence': question.sequence,
                'step_key': page.irg_tfm_step_key,
                'section_title': page.title,
                'title': question.title,
                'description': question.description,
                'question_type': question.question_type,
                'mandatory': question.constr_mandatory,
                'prefill_source': question.irg_tfm_prefill_source,
                'answer_text': prefill.get(question.irg_tfm_prefill_source, ''),
                'option_ids': [Command.create({
                    'template_option_id': option.id,
                    'sequence': option.sequence,
                    'value': option.value,
                }) for option in options],
            }))
        try:
            with self.env.cr.savepoint():
                return Outline.create({
                    'thesis_id': thesis.id,
                    'survey_id': survey.id,
                    'survey_title': survey.title,
                    'version': 0,
                    'state': 'draft',
                    'revision': 0,
                    'current_step': 'proposal',
                    'started_by': self.env.user.id,
                    'started_at': fields.Datetime.now(),
                    'question_ids': question_commands,
                })
        except IntegrityError as exc:
            if getattr(exc.diag, 'constraint_name', None) != _VERSION_CONSTRAINT:
                raise
            Outline.invalidate_model()
            draft = Outline.search([
                ('thesis_id', '=', thesis.id), ('state', '=', 'draft'), ('version', '=', 0),
            ], limit=1)
            if draft:
                return draft
            raise ValidationError(_('No se pudo crear el borrador del Esquema.'))

    @api.model
    def _irg_lock_owned_draft(self, course_id, outline_id):
        thesis = self._irg_lock_owned_configuration(course_id)
        try:
            outline_id = int(outline_id)
        except (TypeError, ValueError):
            outline_id = 0
        draft = self.sudo().search([
            ('id', '=', outline_id),
            ('thesis_id', '=', thesis.id),
            ('state', '=', 'draft'),
            ('version', '=', 0),
        ], limit=1)
        if not draft:
            raise AccessError(_('El borrador solicitado no está disponible.'))
        self.env.cr.execute(
            'SELECT id FROM irg_tfm_esquema WHERE id = %s FOR UPDATE', [draft.id]
        )
        if not self.env.cr.fetchone():
            raise AccessError(_('El borrador solicitado no está disponible.'))
        draft.invalidate_recordset()
        draft = draft.exists()
        if not draft or draft.thesis_id.id != thesis.id or draft.state != 'draft':
            raise AccessError(_('El borrador solicitado no está disponible.'))
        return thesis, draft

    @api.model
    def _irg_assert_revision(self, draft, revision):
        try:
            revision = int(revision)
        except (TypeError, ValueError):
            revision = -1
        if revision != draft.revision:
            raise ValidationError(_(
                'Este borrador fue actualizado desde otra pestaña. Recarga la página '
                'para conservar la versión más reciente.'
            ))

    @api.model
    def _irg_question_answered(self, question):
        if question.question_type in ('simple_choice', 'multiple_choice'):
            return bool(question.selected_option_ids)
        return bool((question.answer_text or '').strip())

    @api.model
    def _irg_answer_values(self, question, value):
        if question.question_type in ('char_box', 'text_box'):
            value = '' if value is None else str(value)
            maximum = (
                _MAX_CHAR_ANSWER if question.question_type == 'char_box'
                else _MAX_TEXT_ANSWER
            )
            if len(value) > maximum:
                raise ValidationError(_(
                    'La respuesta a “%s” supera el máximo de %s caracteres.'
                ) % (question.title, maximum))
            if question.prefill_source == 'student_email' and value.strip():
                if len(email_split(value.strip())) != 1:
                    raise ValidationError(_(
                        'Introduce una única dirección de correo válida.'
                    ))
            return (
                {'answer_text': value, 'selected_option_ids': [Command.clear()]},
                bool(value.strip()),
            )

        raw_ids = value if isinstance(value, (list, tuple, set)) else [value]
        option_ids = []
        for raw_id in raw_ids:
            if raw_id in (False, None, ''):
                continue
            try:
                option_ids.append(int(raw_id))
            except (TypeError, ValueError):
                raise ValidationError(_('La opción seleccionada no es válida.'))
        option_ids = list(dict.fromkeys(option_ids))
        maximum = 1 if question.question_type == 'simple_choice' else _MAX_SELECTED_OPTIONS
        if len(option_ids) > maximum:
            raise ValidationError(_('Has seleccionado demasiadas opciones.'))
        if set(option_ids) - set(question.option_ids.ids):
            raise ValidationError(_('La opción seleccionada no pertenece a la pregunta.'))
        return (
            {'answer_text': False, 'selected_option_ids': [Command.set(option_ids)]},
            bool(option_ids),
        )

    @api.model
    def _irg_portal_save_step(
        self, course_id, outline_id, step_key, revision, answers, advance=False,
    ):
        _thesis, draft = self._irg_lock_owned_draft(course_id, outline_id)
        self._irg_assert_revision(draft, revision)
        if step_key not in _STEP_KEYS:
            raise ValidationError(_('El paso del Esquema no es válido.'))
        questions = draft.question_ids.filtered(lambda item: item.step_key == step_key)
        allowed_ids = set(questions.ids)
        normalized = {}
        for raw_id, value in (answers or {}).items():
            try:
                question_id = int(raw_id)
            except (TypeError, ValueError):
                raise ValidationError(_('La pregunta enviada no es válida.'))
            if question_id not in allowed_ids:
                raise ValidationError(_('La pregunta enviada no pertenece al paso actual.'))
            question = questions.filtered(lambda item: item.id == question_id)
            normalized[question_id] = self._irg_answer_values(question, value)
        projected_total = 0
        for question in draft.question_ids:
            normalized_answer = normalized.get(question.id)
            values = normalized_answer[0] if normalized_answer else False
            answer = values['answer_text'] if values else question.answer_text
            projected_total += len(answer or '')
        if projected_total > _MAX_TOTAL_TEXT:
            raise ValidationError(_(
                'El Esquema supera el máximo total de %s caracteres.'
            ) % _MAX_TOTAL_TEXT)
        if advance:
            missing = questions.filtered(lambda item: (
                item.mandatory
                and not (
                    normalized[item.id][1]
                    if item.id in normalized
                    else self._irg_question_answered(item)
                )
            ))
            if missing:
                raise ValidationError(_(
                    'Debes responder todas las preguntas obligatorias del paso.'
                ))
            index = _STEP_KEYS.index(step_key)
            current_step = _STEP_KEYS[min(index + 1, len(_STEP_KEYS) - 1)]
        else:
            current_step = step_key
        Question = self.env['irg.tfm.esquema.pregunta'].sudo().with_context(
            **{_SERVICE_CONTEXT: True}
        )
        for question in questions:
            if question.id in normalized:
                Question.browse(question.id).write(normalized[question.id][0])
        draft.with_context(**{_SERVICE_CONTEXT: True}).write({
            'revision': draft.revision + 1,
            'current_step': current_step,
        })
        return draft

    @api.model
    def _irg_portal_submit(self, course_id, outline_id, revision):
        thesis, draft = self._irg_lock_owned_draft(course_id, outline_id)
        self._irg_assert_revision(draft, revision)
        missing = draft.question_ids.filtered(
            lambda item: item.mandatory and not self._irg_question_answered(item)
        )
        if missing:
            raise ValidationError(_('Debes responder todas las preguntas obligatorias.'))
        previous = self.sudo().search([
            ('thesis_id', '=', thesis.id), ('state', '=', 'done'),
        ], order='version desc', limit=1)
        now = fields.Datetime.now()
        draft.with_context(**{_SERVICE_CONTEXT: True}).write({
            'state': 'done',
            'version': (previous.version or 0) + 1,
            'submitted_at': now,
            'revision': draft.revision + 1,
        })
        self.env['mail.message'].sudo().create({
            'model': 'tesis.model',
            'res_id': thesis.id,
            'record_name': thesis.display_name,
            'message_type': 'comment',
            'subtype_id': self.env.ref('mail.mt_note').id,
            'author_id': self.env.user.partner_id.id,
            'subject': _('Esquema TFM enviado'),
            'body': _('Esquema TFM enviado: versión %s, fecha %s.')
            % (draft.version, fields.Datetime.to_string(now)),
            'partner_ids': False,
        })
        return draft


class IrgTfmEsquemaPregunta(models.Model):
    _name = 'irg.tfm.esquema.pregunta'
    _description = 'Pregunta congelada del Esquema TFM'
    _order = 'sequence, id'

    outline_id = fields.Many2one(
        'irg.tfm.esquema', required=True, readonly=True, index=True, ondelete='restrict',
    )
    template_question_id = fields.Many2one(
        'survey.question', readonly=True, ondelete='set null',
    )
    sequence = fields.Integer(required=True, readonly=True)
    step_key = fields.Selection(_STEP_SELECTION, required=True, readonly=True, index=True)
    section_title = fields.Char(required=True, readonly=True)
    title = fields.Char(required=True, readonly=True)
    description = fields.Html(readonly=True, sanitize=True)
    question_type = fields.Selection(
        [
            ('char_box', 'Texto corto'),
            ('text_box', 'Texto largo'),
            ('simple_choice', 'Selección única'),
            ('multiple_choice', 'Selección múltiple'),
        ],
        required=True,
        readonly=True,
    )
    mandatory = fields.Boolean(readonly=True)
    prefill_source = fields.Selection(
        [
            ('student_name', 'Nombre del alumno'),
            ('student_email', 'Correo del alumno'),
            ('master_name', 'Máster de la matrícula'),
        ],
        readonly=True,
    )
    answer_text = fields.Text(readonly=True)
    option_ids = fields.One2many(
        'irg.tfm.esquema.opcion', 'question_id', string='Opciones', readonly=True,
    )
    selected_option_ids = fields.Many2many(
        'irg.tfm.esquema.opcion',
        'irg_tfm_outline_question_option_rel',
        'question_id',
        'option_id',
        string='Opciones seleccionadas',
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get(_SERVICE_CONTEXT):
            raise AccessError(_(
                'TFM outline questions can only be created by the protected service.'
            ))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(_SERVICE_CONTEXT):
            raise AccessError(_('TFM outline history is immutable.'))
        if set(vals) - {'answer_text', 'selected_option_ids'}:
            raise AccessError(_('TFM outline history is immutable.'))
        if any(question.outline_id.state != 'draft' for question in self):
            raise AccessError(_('TFM outline history is immutable.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(_('TFM outline history is immutable.'))

    def copy(self, default=None):
        raise AccessError(_('TFM outline history is immutable.'))


class IrgTfmEsquemaOpcion(models.Model):
    _name = 'irg.tfm.esquema.opcion'
    _description = 'Opción congelada del Esquema TFM'
    _rec_name = 'value'
    _order = 'sequence, id'

    question_id = fields.Many2one(
        'irg.tfm.esquema.pregunta', required=True, readonly=True, index=True,
        ondelete='restrict',
    )
    template_option_id = fields.Many2one(
        'survey.question.answer', readonly=True, ondelete='set null',
    )
    sequence = fields.Integer(required=True, readonly=True)
    value = fields.Char(required=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get(_SERVICE_CONTEXT):
            raise AccessError(_(
                'TFM outline options can only be created by the protected service.'
            ))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_('TFM outline history is immutable.'))

    def unlink(self):
        raise AccessError(_('TFM outline history is immutable.'))

    def copy(self, default=None):
        raise AccessError(_('TFM outline history is immutable.'))
