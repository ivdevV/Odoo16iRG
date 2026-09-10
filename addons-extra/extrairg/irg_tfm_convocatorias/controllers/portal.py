import base64

from odoo import http, _
from odoo.exceptions import AccessError, ValidationError
from odoo.http import content_disposition, request

from odoo.addons.irg_course_portal_tiles_diplomado_hide.controllers.main import (
    IrgTFMControllerDiplomado,
)
from odoo.addons.irg_course_convocatorias_v2.controllers.main import (
    CourseConvocatoriasSlides,
)
from odoo.addons.irg_online_subject_portal_visibility.controllers.main import (
    OnlineSubjectVisibilitySlides,
)
from odoo.addons.irg_practice_slide_restrictions.controllers.main import (
    WebsiteSlidesPracticeRestrictions,
)
from odoo.addons.isep_tesis_model.controllers.my_tesis_model2 import (
    TesisReviewPortal as LegacyTesisReviewPortal,
    preparteTesisReviewPortal as LegacyTesisPortalCounter,
)
from odoo.addons.isep_tesis_model.controllers.my_tesis_model_new import (
    TessisreviewwPortal as LegacyTesisNewPortal,
)
from odoo.addons.website_slides.controllers.main import WebsiteSlides


class WebsiteSlidesTfmRestrictions(
        OnlineSubjectVisibilitySlides, WebsiteSlidesPracticeRestrictions):
    """Compose exact TFM routing with every existing eLearning guard."""

    @http.route([
        '/slides/<model("slide.channel"):channel>',
        '/slides/<model("slide.channel"):channel>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>',
        '/slides/<model("slide.channel"):channel>/tag/<model("slide.tag"):tag>/page/<int:page>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>',
        '/slides/<model("slide.channel"):channel>/category/<model("slide.slide"):category>/page/<int:page>',
    ], type='http', auth='public', website=True, sitemap=WebsiteSlides.sitemap_slide)
    def channel(
        self,
        channel,
        category=None,
        tag=None,
        page=1,
        slide_category=None,
        uncategorized=False,
        sorting=None,
        search=None,
        **kwargs
    ):
        user = request.env.user
        if not user.has_group('base.group_user') and channel.sudo()._irg_tfm_is_configured_family():
            thesis, effective = channel.sudo()._irg_tfm_route_for_user(user)
            if not thesis or not effective:
                return request.not_found()
            if channel.id != effective.id:
                return request.redirect('/slides/%s' % effective.id)
            return WebsiteSlides.channel(
                self,
                channel,
                category=category,
                tag=tag,
                page=page,
                slide_category=slide_category,
                uncategorized=uncategorized,
                sorting=sorting,
                search=search,
                **kwargs
            )
        return super().channel(
            channel,
            category=category,
            tag=tag,
            page=page,
            slide_category=slide_category,
            uncategorized=uncategorized,
            sorting=sorting,
            search=search,
            **kwargs
        )

    @http.route(
        ['/slides/slide/<model("slide.slide"):slide>'],
        type='http',
        auth='public',
        website=True,
        sitemap=True,
    )
    def slide_view(self, slide, **kwargs):
        user = request.env.user
        channel = slide.sudo().channel_id
        is_tfm_family = bool(
            channel and channel._irg_tfm_is_configured_family()
        )
        if not user.has_group('base.group_user') and is_tfm_family:
            thesis, effective = channel._irg_tfm_route_for_user(user)
            if not thesis or not effective:
                return request.not_found()
            if channel.id != effective.id:
                return self._irg_tfm_redirect_slide(slide.sudo(), effective)

        if slide.sudo().irg_has_tfm_requirement():
            if user._is_public():
                return request.redirect(
                    '/web/login?redirect=/slides/slide/%s' % slide.id
                )
            if not slide.is_user_allowed_by_tfm_convocation(user):
                return request.render(
                    'irg_tfm_convocatorias.slide_tfm_restriction_error',
                    {'slide': slide},
                )
        # For a TFM family, the exact enrollment above replaces V2's global
        # admission heuristic. Continue after that controller so scheduled,
        # batch, practice, debtor and prerequisite guards still execute. For a
        # regular channel, preserve the complete Online/V2 chain unchanged.
        if is_tfm_family:
            return super(CourseConvocatoriasSlides, self).slide_view(
                slide, **kwargs
            )
        return super().slide_view(slide, **kwargs)

    def _irg_tfm_redirect_slide(self, slide, effective_channel):
        if effective_channel.irg_homeclass_channel_id:
            counterpart = request.env['slide.slide'].sudo().search([
                ('channel_id', '=', effective_channel.id),
                ('irg_original_slide_id', '=', slide.id),
            ], limit=1)
        else:
            counterpart = slide.irg_original_slide_id.sudo()
            if counterpart and counterpart.channel_id != effective_channel:
                counterpart = request.env['slide.slide']
        if counterpart:
            return request.redirect('/slides/slide/%s' % counterpart.id)
        return request.redirect('/slides/%s' % effective_channel.id)

    def _get_slide_detail(self, slide):
        values = super()._get_slide_detail(slide)
        user = request.env.user
        blocked = set()
        channel = slide.sudo().channel_id
        if channel:
            slides = channel.slide_ids.sudo()
            for item in slides:
                if item.irg_has_tfm_requirement() and not item.is_user_allowed_by_tfm_convocation(user):
                    blocked.add(item.id)
        values['tfm_blocked_slide_ids'] = blocked
        return values


class IrgTfmSecurePortal(IrgTFMControllerDiplomado):
    _outline_steps = ('proposal', 'approach', 'results')
    _outline_step_labels = {
        'proposal': 'Datos y propuesta',
        'approach': 'Planteamiento',
        'results': 'Resultados y fuentes',
    }

    def _frozen_outline_step_labels(self, outline):
        labels = dict(self._outline_step_labels)
        if outline:
            for question in outline.question_ids.sorted(
                key=lambda item: (item.sequence, item.id)
            ):
                if question.step_key in labels and question.section_title:
                    labels[question.step_key] = question.section_title
        return labels

    def _page_values(self, thesis, error=None):
        course = thesis.course_id.course_id
        convocation = thesis.irg_tfm_convocation_id
        today = request.env['irg.tfm.entrega']._irg_madrid_today()
        partial_open = bool(
            convocation
            and convocation.active
            and convocation.partial_open_date
            and convocation.partial_close_date
            and convocation.partial_open_date <= today <= convocation.partial_close_date
        )
        final_open = bool(
            convocation
            and convocation.active
            and convocation.final_open_date
            and convocation.final_close_date
            and convocation.final_open_date <= today <= convocation.final_close_date
        )
        deliveries = thesis.irg_tfm_submission_ids.sorted(
            key=lambda delivery: (delivery.submitted_at, delivery.id), reverse=True,
        )
        outlines = request.env['irg.tfm.esquema'].sudo().search([
            ('thesis_id', '=', thesis.id),
        ], order='submitted_at desc, started_at desc, id desc')
        channel = request.env['slide.channel']
        if convocation and convocation.active and course.irg_tfm_channel_id:
            resolved_thesis, effective = course.irg_tfm_channel_id._irg_tfm_route_for_user(
                request.env.user,
            )
            if resolved_thesis.id == thesis.id:
                channel = effective

        def display_date(value):
            return value.strftime('%d/%m/%Y') if value else '-'

        outline_draft = outlines.filtered(
            lambda outline: outline.state == 'draft'
        )[:1]
        return {
            'thesis': thesis,
            'course': course,
            'convocation': convocation,
            'outline_versions': outlines.filtered(lambda outline: outline.state == 'done'),
            'outline_draft': outline_draft,
            'outline_step_labels': self._frozen_outline_step_labels(outline_draft),
            'legacy_outline_deliveries': deliveries.filtered(
                lambda delivery: delivery.stage == 'outline'
            ),
            'partial_deliveries': deliveries.filtered(lambda delivery: delivery.stage == 'partial'),
            'final_deliveries': deliveries.filtered(lambda delivery: delivery.stage == 'final'),
            'outline_open': not convocation,
            'partial_open': partial_open,
            'final_open': final_open,
            'elearning_url': channel.website_url if channel else False,
            'partial_open_label': display_date(
                convocation.partial_open_date if convocation else False,
            ),
            'partial_close_label': display_date(
                convocation.partial_close_date if convocation else False,
            ),
            'final_open_label': display_date(
                convocation.final_open_date if convocation else False,
            ),
            'final_close_label': display_date(
                convocation.final_close_date if convocation else False,
            ),
            'error': error,
        }

    def _owned_outline(self, thesis, outline_id, draft_only=False):
        try:
            outline_id = int(outline_id)
        except (TypeError, ValueError):
            return request.env['irg.tfm.esquema']
        domain = [('id', '=', outline_id), ('thesis_id', '=', thesis.id)]
        if draft_only:
            domain.extend([('state', '=', 'draft'), ('version', '=', 0)])
        return request.env['irg.tfm.esquema'].sudo().search(domain, limit=1)

    def _outline_values(self, thesis, outline, step=None, review=False, error=None):
        step = step if step in self._outline_steps else outline.current_step
        if step not in self._outline_steps:
            step = self._outline_steps[0]
        position = self._outline_steps.index(step)
        step_labels = self._frozen_outline_step_labels(outline)
        return {
            'thesis': thesis,
            'course': thesis.course_id.course_id,
            'outline': outline,
            'editable': bool(outline.state == 'draft' and not thesis.irg_tfm_convocation_id),
            'review': bool(review),
            'step_key': step,
            'step_keys': self._outline_steps,
            'step_labels': step_labels,
            'step_label': step_labels[step],
            'step_number': position + 1,
            'previous_step': self._outline_steps[position - 1] if position else False,
            'next_step': (
                self._outline_steps[position + 1]
                if position + 1 < len(self._outline_steps) else False
            ),
            'step_questions': outline.question_ids.filtered(
                lambda question: question.step_key == step
            ),
            'error': error,
        }

    @http.route(
        ['/campus/course/<int:course_id>/tfm'],
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def tfm_page(self, course_id, **kwargs):
        thesis = request.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=False,
        )
        if not thesis:
            return request.not_found()
        if thesis.course_id.course_id.is_diplomado():
            return request.render('website.403')
        return request.render(
            'irg_tfm_convocatorias.tfm_mycampus_page',
            self._page_values(thesis),
        )

    @http.route(
        ['/campus/course/<int:course_id>/tfm/outline/start'],
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def tfm_outline_start(self, course_id, **post):
        thesis = request.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=False,
        )
        if not thesis or thesis.course_id.course_id.is_diplomado():
            return request.not_found()
        try:
            outline = request.env['irg.tfm.esquema']._irg_portal_start(course_id)
        except AccessError:
            return request.not_found()
        except ValidationError as exc:
            return request.render(
                'irg_tfm_convocatorias.tfm_mycampus_page',
                self._page_values(thesis, error=str(exc)),
            )
        return request.redirect(
            '/campus/course/%s/tfm/outline/%s' % (course_id, outline.id)
        )

    @http.route(
        [
            '/campus/course/<int:course_id>/tfm/outline/<int:outline_id>',
        ],
        type='http', auth='user', website=True, methods=['GET'],
    )
    def tfm_outline_page(self, course_id, outline_id, step=None, review=None, **kwargs):
        thesis = request.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=False,
        )
        if not thesis or thesis.course_id.course_id.is_diplomado():
            return request.not_found()
        outline = self._owned_outline(thesis, outline_id)
        if not outline:
            return request.not_found()
        return request.render(
            'irg_tfm_convocatorias.tfm_outline_form',
            self._outline_values(thesis, outline, step=step, review=bool(review)),
        )

    @http.route(
        ['/campus/course/<int:course_id>/tfm/outline/<int:outline_id>/save'],
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def tfm_outline_save(self, course_id, outline_id, **post):
        thesis = request.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=False,
        )
        if not thesis or thesis.course_id.course_id.is_diplomado():
            return request.not_found()
        outline = self._owned_outline(thesis, outline_id, draft_only=True)
        if not outline:
            return request.not_found()
        step = post.get('step')
        if step not in self._outline_steps:
            return request.not_found()
        questions = outline.question_ids.filtered(
            lambda question: question.step_key == step
        )
        answers = {}
        for question in questions:
            key = 'question_%s' % question.id
            if question.question_type in ('simple_choice', 'multiple_choice'):
                answers[str(question.id)] = request.httprequest.form.getlist(key)
            else:
                answers[str(question.id)] = post.get(key, '')
        action = post.get('action')
        if action not in ('save', 'next', 'review'):
            return request.not_found()
        try:
            outline = request.env['irg.tfm.esquema']._irg_portal_save_step(
                course_id,
                outline.id,
                step,
                post.get('revision'),
                answers,
                advance=action in ('next', 'review'),
            )
        except AccessError:
            return request.not_found()
        except ValidationError as exc:
            outline.invalidate_recordset()
            return request.render(
                'irg_tfm_convocatorias.tfm_outline_form',
                self._outline_values(thesis, outline, step=step, error=str(exc)),
            )
        if action == 'save':
            return request.redirect('/campus/course/%s/tfm' % course_id)
        if action == 'review':
            return request.redirect(
                '/campus/course/%s/tfm/outline/%s?review=1' % (course_id, outline.id)
            )
        return request.redirect(
            '/campus/course/%s/tfm/outline/%s?step=%s'
            % (course_id, outline.id, outline.current_step)
        )

    @http.route(
        ['/campus/course/<int:course_id>/tfm/outline/<int:outline_id>/submit'],
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def tfm_outline_submit(self, course_id, outline_id, **post):
        thesis = request.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=False,
        )
        if not thesis or thesis.course_id.course_id.is_diplomado():
            return request.not_found()
        try:
            request.env['irg.tfm.esquema']._irg_portal_submit(
                course_id, outline_id, post.get('revision'),
            )
        except AccessError:
            return request.not_found()
        except ValidationError as exc:
            outline = self._owned_outline(thesis, outline_id)
            if not outline:
                return request.not_found()
            return request.render(
                'irg_tfm_convocatorias.tfm_outline_form',
                self._outline_values(thesis, outline, review=True, error=str(exc)),
            )
        return request.redirect('/campus/course/%s/tfm' % course_id)

    @http.route(
        ['/campus/course/<int:course_id>/tfm/submit'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def tfm_submit(self, course_id, **post):
        thesis = request.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=False,
        )
        if not thesis:
            return request.not_found()
        upload = request.httprequest.files.get('file')
        try:
            if post.get('stage') == 'outline':
                raise ValidationError(_(
                    'Los nuevos Esquemas se envían mediante el cuestionario TFM.'
                ))
            if not upload:
                raise ValidationError(_('Select a file to submit.'))
            request.env['irg.tfm.entrega']._irg_create_portal_submission(
                course_id,
                post.get('stage'),
                upload.stream.read((20 * 1024 * 1024) + 1),
                upload.filename,
                upload.mimetype,
                post.get('comment'),
            )
        except AccessError:
            return request.not_found()
        except ValidationError as exc:
            return request.render(
                'irg_tfm_convocatorias.tfm_mycampus_page',
                self._page_values(thesis, error=str(exc)),
            )
        return request.redirect('/campus/course/%s/tfm' % course_id)

    @http.route(
        ['/campus/tfm/delivery/<int:delivery_id>/download'],
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def tfm_download(self, delivery_id, **kwargs):
        delivery = request.env['irg.tfm.entrega']._irg_portal_owned_delivery(
            delivery_id, raise_missing=False,
        )
        if not delivery or not delivery.attachment_id:
            return request.not_found()
        attachment = delivery.attachment_id
        if (
            attachment.res_model != 'irg.tfm.entrega'
            or attachment.res_id != delivery.id
            or attachment.type != 'binary'
            or attachment.public
        ):
            return request.not_found()
        raw = attachment.raw or (attachment.datas and base64.b64decode(attachment.datas))
        if not raw:
            return request.not_found()
        return request.make_response(raw, headers=[
            ('Content-Type', attachment.mimetype or 'application/octet-stream'),
            ('Content-Disposition', content_disposition(attachment.name)),
            ('X-Content-Type-Options', 'nosniff'),
        ])


class IrgTfmLegacyNewNeutralizer(LegacyTesisNewPortal):
    @http.route(
        ['/my/tesis_models/new'],
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def create_tesis_model(self, **kwargs):
        if request.httprequest.method == 'POST':
            return request.not_found()
        return request.redirect('/campus')


class IrgTfmLegacyCounterNeutralizer(LegacyTesisPortalCounter):
    def _prepare_home_portal_values(self, counters):
        safe_counters = [counter for counter in counters if counter != 'tesis_models_count']
        values = super(LegacyTesisPortalCounter, self)._prepare_home_portal_values(
            safe_counters,
        )
        values.pop('tesis_models_count', None)
        return values


class IrgTfmLegacyRoutesNeutralizer(LegacyTesisReviewPortal):
    @http.route(
        ['/my/tesis_models2'], type='http', auth='user', website=True, methods=['GET'],
    )
    def list_tesis_models(self, **kwargs):
        return request.redirect('/campus')

    @http.route(
        ['/my/tesis_models2/accept'],
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def accept_tesis_model(self, **kwargs):
        return request.not_found()

    @http.route(
        ['/my/tesis_models2/decline'],
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def decline_tesis_model(self, **kwargs):
        return request.not_found()

    @http.route(
        ['/my/tesis_model/<int:request_id>'],
        type='http', auth='user', website=True, methods=['GET'],
    )
    def tesis_model_details(self, request_id, **kwargs):
        return request.not_found()

    @http.route(
        ['/web/submit_documenttr'],
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def submit_documenttr(self, **kwargs):
        return request.not_found()

    @http.route(
        ['/my/notificacionestr/download/<string:attachment_id>'],
        type='http', auth='user', website=True, methods=['GET'],
    )
    def download_attachment(self, attachment_id, **kwargs):
        return request.not_found()

    @http.route(
        ['/my/notificacionestr/borrar/<string:attachment_id>/<string:tesis_model_id>'],
        type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True,
    )
    def borrar_attachment(self, attachment_id, tesis_model_id, **kwargs):
        return request.not_found()

    @http.route(
        ['/my/notificacionestr/comment/<int:attachment_id>'],
        type='http', auth='user', website=True, methods=['GET'],
    )
    def view_attachment_comment(self, attachment_id, **kwargs):
        return request.not_found()
