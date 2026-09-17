# Spec — filtro de modalidades de prácticas para másteres online

## Objetivo

En la solicitud de prácticas del campus, un alumno de máster **online** solo puede elegir:

- Convalidación por experiencia (`validation`)
- Convalidación por TFM (`tfm_validation`)
- Prácticas asíncronas (`homeclass_asincronas`)

El resto de modalidades (presencial España/origen, distancia, HomeClass síncronas, etc.) no se muestran y el servidor rechaza el POST si llegan igual.

## Detección online (lote)

Referencia: `op.student.course.batch_id.code` (no el nombre del curso, no `irg_content_modality`).

1. Código vacío → no es online (sin filtro).
2. Si el código (mayúsculas) **empieza** por `MONLHC` o `MONLPRS` → **no** es online (Neurologopedia HomeClass / Presencial). `MONL` ya contiene la subcadena `ONL`.
3. En cualquier otro caso, si el código contiene `ONL` → es online. Incluye `MONLONL…`.

No usar la regla `'ONL' in code and 'MONL' not in code`: excluiría la variante online real `MONLONL`.

Staff en backend no está limitado: puede asignar cualquier tipo.

## Superficies

- Portal `/my/practice_requests/new`: data-attrs + JS (después del script legacy que resetea `hidden`).
- `practice.request` create/write con usuario portal: `ValidationError` si el tipo no está permitido. El create del campus usa `sudo()` pero conserva el uid portal.

## Fuera de alcance

- No editar `isep_practices_2` ni el JS hardcodeado de `MAESTRÍA EN PSICOLOGÍA CLÍNICA` / id 2.
- No crear registros de catálogo (si no existe asíncronas en datos, no saldrá hasta que exista).
- No cambiar el filtro de eLearning (módulo B).
