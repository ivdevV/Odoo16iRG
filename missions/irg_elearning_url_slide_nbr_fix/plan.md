# irg_elearning_url_slide_nbr_fix

## Alcance

Corregir el error `KeyError: 'nbr_url'` al guardar contenidos URL en eLearning.

## Diagnostico

El traceback muestra que `website_slides.models.slide_slide._compute_slides_statistics` intenta actualizar el campo `nbr_url` en `slide.slide`. La implementacion inicial anadio `slide.channel.nbr_url`, pero falta el contador equivalente en `slide.slide`.

## Clasificacion de Complejidad

Tier: `trivial`.

Justificacion: cambio localizado en 1 archivo de codigo, sin logica nueva, sin migraciones, autenticacion, concurrencia, secretos ni borrado de datos.

## Plan

1. Anadir `nbr_url = fields.Integer(string='URL', store=True)` en la clase heredada `slide.slide`.
2. Validar sintaxis Python.
3. Validar instalacion/tests del modulo con `docker-compose.local.yml`.
4. Generar `verification.json` con evidencia.
5. Commit y push del fix a `Dev_iRG`.

## Criterios de Aceptacion

- No aparece `KeyError: 'nbr_url'` al crear/guardar slide URL.
- El modulo instala y ejecuta tests enfocados sin errores.
