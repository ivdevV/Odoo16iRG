# Micro-Spec: irg_exam_score_100

## Objetivo
Normalizar automaticamente examenes/certificaciones basados en `survey.survey` para que su escala interna cierre en 100 puntos, manteniendo la libreta academica en escala 10.

## Alcance
- Nuevo modulo en `addons-extra/extrairg/irg_exam_score_100`.
- Herencia de `survey.survey`, `survey.question`, `survey.question.answer`.
- Configuracion por encuesta para auto escala 100.
- Recalculo automatico al crear/editar/eliminar preguntas/respuestas.
- Boton manual de recálculo en formulario de encuesta.

## No Alcance
- No modificar modulos existentes en `addons_uisep` o core.
- No migrar `isep_gradebook` de escala 10 a 100.
- No implementar cambios sobre flujo `op.quiz`.

## Regla de Negocio
Si el examen tiene `N` preguntas puntuables y objetivo `T` (default 100), cada pregunta vale `T/N`.

## Ejemplo
- 50 preguntas, objetivo 100 -> 2 puntos por pregunta.

## Riesgos
- Preguntas no puntuables mezcladas con puntuables.
- Preguntas con multiples respuestas correctas.
- Redondeo acumulado.

## Mitigacion
- Filtrar solo preguntas puntuables.
- Distribuir score de pregunta entre respuestas correctas.
- Ajustar residuo en la ultima pregunta para cerrar suma exacta.
