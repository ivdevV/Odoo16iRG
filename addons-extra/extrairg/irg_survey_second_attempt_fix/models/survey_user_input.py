import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SurveyUserInputSecondAttemptFix(models.Model):
    _inherit = 'survey.user_input'

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

        # Solo aplicar corrección en el momento en que se cierra el intento.
        # _mark_done() llama write({'state': 'done', 'end_datetime': ...}).
        if values.get('state') != 'done':
            return result

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
                    "irg_survey_second_attempt_fix: corrigiendo scoring_success "
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

        return result
