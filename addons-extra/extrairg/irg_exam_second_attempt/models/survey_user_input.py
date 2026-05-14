import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SurveyUserInputExamSecondAttempt(models.Model):
    _inherit = 'survey.user_input'

    def _irg_get_exam_score_for_gradebook(self):
        self.ensure_one()
        if 'answer_score_total' in self._fields:
            return self.answer_score_total or 0.0
        return round((self.scoring_percentage or 0.0) / 10.0, 2)

    def _irg_get_exam_attempts_for_gradebook(self):
        self.ensure_one()
        attempts = self
        if self.slide_partner_id:
            attempts = self.slide_partner_id.user_input_ids.filtered(
                lambda attempt: (
                    attempt.survey_id == self.survey_id
                    and attempt.survey_type == 'exam'
                    and not attempt.test_entry
                    and attempt.state == 'done'
                )
            )
        return attempts | self

    def _irg_sync_exam_gradebook_result(self):
        if not all(
            field_name in self._fields
            for field_name in (
                'result_id',
                'gradebook_student_id',
                'gradebook_subject_id',
                'admission_id',
                'op_subject_id',
                'course_id',
                'channel_partner_id',
            )
        ):
            return

        for record in self.filtered(
            lambda attempt: (
                attempt.survey_type == 'exam'
                and not attempt.test_entry
                and attempt.state == 'done'
            )
        ):
            if (
                (not record.admission_id or not record.op_subject_id)
                and hasattr(record, 'compute_slide_channel_partner')
            ):
                record.compute_slide_channel_partner()

            if not (
                record.partner_id
                and record.admission_id
                and record.op_subject_id
                and record.course_id
                and record.channel_partner_id
            ):
                continue

            # sudo(): usa la misma regla funcional de isep_gradebook para crear
            # o localizar libreta/asignatura académica aunque el intento llegue
            # desde el portal del alumno.
            gradebook_data = record.channel_partner_id.sudo().search_gradebook_subject(
                record.partner_id,
                record.admission_id,
                record.course_id,
                record.op_subject_id,
            )
            gradebook_student = gradebook_data.get('gradebook_student_id')
            gradebook_subject = gradebook_data.get('gradebook_subject_id')
            if not gradebook_subject:
                continue

            attempts = record._irg_get_exam_attempts_for_gradebook()
            score_for_gradebook = max(
                attempts.mapped(
                    lambda attempt: attempt._irg_get_exam_score_for_gradebook()
                )
                or [record._irg_get_exam_score_for_gradebook()]
            )

            result = record.result_id.filtered(
                lambda res: res.gradebook_subject_id == gradebook_subject
            )[:1]
            if not result:
                # sudo(): los resultados de libreta son registros académicos;
                # el alumno puede finalizar el examen desde portal sin permisos
                # directos sobre app.gradebook.result.
                result = self.env['app.gradebook.result'].sudo().search([
                    ('gradebook_subject_id', '=', gradebook_subject.id),
                    ('survey_type', '=', 'exam'),
                    ('survey_user_input_id', 'in', attempts.ids),
                ], limit=1)

            result_values = {
                'name': record.survey_id.title,
                'survey_user_input_id': record.id,
                'channel_id': record.channel_id.id,
                'channel_partner_id': record.channel_partner_id.id,
                'scoring_total': score_for_gradebook,
                'gradebook_subject_id': gradebook_subject.id,
                'survey_type': 'exam',
                'description': '%s - %s' % (
                    record.admission_id.application_number or 'N/A',
                    record.course_id.name or 'N/A',
                ),
                'rated_by': self.env.user.partner_id.id or False,
                'comment': record.comment,
            }
            if result:
                result.sudo().write(result_values)
            else:
                result = self.env['app.gradebook.result'].sudo().create(result_values)

            # sudo(): enlaza intentos previos del mismo examen al resultado de
            # libreta aunque el cierre venga desde el usuario portal. _write()
            # evita el write() singleton de isep_gradebook en recordsets de
            # varios intentos; la nota ya se actualizo arriba en result.write().
            attempts.sudo()._write({
                'result_id': result.id,
                'gradebook_student_id': (
                    gradebook_student.id if gradebook_student else False
                ),
                'gradebook_subject_id': gradebook_subject.id,
                'rated_by': self.env.user.partner_id.id or False,
            })

    def _irg_should_sync_exam_gradebook(self, values):
        if self.env.context.get('irg_skip_gradebook_sync'):
            return False
        trigger_fields = {
            'state',
            'scoring_percentage',
            'scoring_total',
            'answer_score_total',
            'comment',
            'slide_partner_id',
            'slide_id',
            'partner_id',
            'admission_id',
            'op_subject_id',
            'course_id',
            'channel_partner_id',
        }
        return bool(trigger_fields.intersection(values))

    # ------------------------------------------------------------------
    # BUG-FIX 1: _check_for_failed_attempt siempre retorna True
    # ------------------------------------------------------------------
    # isep_survey._check_for_failed_attempt() devuelve True sin realizar la
    # lógica de reactivación del intento fallido que define el núcleo de Odoo.
    #
    # En el núcleo, devolver True le indica al controlador de
    # website_slides_survey que el antiguo intento fallido HA SIDO reactivado
    # (se resetea a 'new' y se le da el nuevo token), y lo re-fetcha. Como
    # isep_survey devuelve True sin hacer nada, el controlador re-fetchea y
    # encuentra el nuevo intento limpio — lo que casualmente funciona. Sin
    # embargo, hay un problema colateral importante:
    #
    # El núcleo de _check_for_failed_attempt() también usa
    # scoring_success=False para identifizcar intentos fallidos.
    # Si scoring_success siempre es False (bug 2), el núcleo NUNCA podría
    # identificar un intento superado como "no fallido", lo que afecta a
    # múltiples flujos del core de website_slides_survey.
    #
    # FIX: para survey_type exam/assignment, retornar False explícitamente.
    # Esto indica al controlador "usa el intento actual tal cual" (sin
    # re-fetch), que es el comportamiento correcto para exámenes académicos
    # donde siempre se crea un intento nuevo limpio.
    # ------------------------------------------------------------------

    def _check_for_failed_attempt(self):
        self.ensure_one()
        if self.survey_type in ('exam', 'assignment'):
            # Para exámenes académicos: nunca reactivar un intento anterior.
            # El controlador usará el nuevo intento limpio directamente.
            # certification=False en estos surveys, por lo que la lógica de
            # reactivación del núcleo no aplica.
            return False
        return super()._check_for_failed_attempt()

    # ------------------------------------------------------------------
    # BUG-FIX 2: scoring_success siempre forzado a False
    # ------------------------------------------------------------------
    # isep_survey.write() añade scoring_success=False a cada escritura de
    # intentos tipo exam/assignment para evitar que Odoo genere certificados
    # automáticamente. Sin embargo, certification=False ya está forzado por
    # isep_survey.survey.write(), por lo que el certificado NUNCA se genera
    # independientemente del valor de scoring_success.
    #
    # Forzar scoring_success=False provoca:
    #   1. La página de resultado muestra "suspenso" aunque el alumno haya
    #      aprobado, ya que website_slides_survey usa scoring_success para
    #      determinar el estado del alumno.
    #   2. La lógica de website_slides_survey que busca el "último intento
    #      superado" (scoring_success=True) nunca encuentra ninguno y puede
    #      mostrar el primer intento como resultado fallback.
    #   3. _check_for_failed_attempt() del núcleo busca entradas con
    #      scoring_success=False para identificar fallos; con todos en False,
    #      todos los intentos parecen fallidos.
    #
    # FIX: después de la cadena super() (que incluye el forzado de
    # isep_survey), corrijo scoring_success usando _write() para que refleje
    # el resultado real. _write() escribe a nivel bajo sin pasar por
    # write() hooks, evitando bucles y respetando el resto de la lógica.
    # ------------------------------------------------------------------

    def write(self, values):
        result = super().write(values)

        if values.get('state') == 'done':
            for record in self.filtered(
                lambda r: r.survey_type in ('exam', 'assignment')
            ):
                survey = record.survey_id
                # Solo aplica a surveys con puntuación (no 'no_scoring').
                if survey.scoring_type not in (
                    'scoring_without_answers',
                    'scoring_with_answers',
                ):
                    continue

                # Calcular el scoring_success correcto basado en la nota real.
                # record.scoring_percentage ya tiene el valor actualizado porque
                # _compute_scoring_values() se disparó cuando se guardaron las
                # respuestas (user_input_line_ids.answer_score cambió).
                correct_success = (
                    record.scoring_percentage >= survey.scoring_success_min
                )

                if record.scoring_success != correct_success:
                    _logger.info(
                        "irg_exam_second_attempt: corrigiendo scoring_success "
                        "%s → %s para user_input %s "
                        "(scoring_percentage=%.2f, scoring_success_min=%.2f)",
                        record.scoring_success,
                        correct_success,
                        record.id,
                        record.scoring_percentage,
                        survey.scoring_success_min,
                    )
                    # _write() escribe directamente a la BD sin pasar por write()
                    # ni disparar recomputaciones encadenadas de scoring_success.
                    record._write({'scoring_success': correct_success})

        if self._irg_should_sync_exam_gradebook(values):
            self.filtered(
                lambda record: record.state == 'done'
            )._irg_sync_exam_gradebook_result()

        return result
