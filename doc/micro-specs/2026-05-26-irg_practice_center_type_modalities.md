# Micro-Spec: IRG Practice Center Type Modalities (2026-05-26)

## Objetivo

Actualizar las opciones del campo `type_of_practice` del modelo `practice.center.type` sin modificar el modulo base `isep_practices_2`.

## Alcance

- Nuevo modulo `irg_practice_center_type_modalities` en `addons-extra/extrairg/`.
- Herencia del modelo `practice.center.type` para ajustar las etiquetas visibles:
  - `on_site`: `Presencial en España`.
  - `validation`: `Convalidación por experiencia`.
- Nuevas opciones de seleccion:
  - `on_site_origin`: `Presencial País de Origen`.
  - `tfm_validation`: `Convalidación por TFM`.
- Nuevos registros disponibles para las dos opciones nuevas.
- Las opciones HomeClass existentes se mantienen sin cambios.

## Validacion

- Test automatizado del modulo con Odoo local mediante `docker-compose.local.yml`.
- El test verifica etiquetas de seleccion, registros XML y `name_get()`.

## Rollback

Desinstalar `irg_practice_center_type_modalities` o revertir el commit del modulo y actualizar la base de datos.
