# Design: QWeb seguro en el tile de certificados del campus

Fecha: 2026-09-04

## Problema

Tras actualizar `irg_campus_certificates_portal` en beta, `/campus/course/<id>`
devuelve HTTP 500:

```
TypeError: 'NoneType' object is not callable
Template: isep_website_custom.user_profile_content_details
Node: <div t-if="not hasattr(course_id, 'irg_is_diplomado') or not course_id.irg_is_diplomado()" ... name="certificates_and_diplomas"/>
```

En Odoo 16, `hasattr` no está en `_BUILTINS` de `safe_eval`. QWeb evalúa
`hasattr(...)` como `None(...)`. Desinstalar el módulo de fecha de diplomados
no revierte la vista de la dependencia.

El `UncaughtPromiseError` de `getUserModelName` es el editor web del backend
sobre esa misma página 500. Fuera de alcance.

## Decisión

Nuevo módulo `irg_campus_certificates_tile_qweb_fix` que hereda
`irg_campus_certificates_portal.user_profile_content_details_certificates_tile`
y sustituye el `t-if` por `not course_id.is_diplomado()`.

No se edita `irg_campus_certificates_portal`.

## Dependencias

- `irg_campus_certificates_portal` — vista a heredar
- `irg_course_portal_tiles_diplomado_hide` — método `op.course.is_diplomado()`
  ya usado en las tiles hermanas de Prácticas y TFM

`auto_install: True` para que, con ambas dependencias instaladas, el arreglo
entre al actualizar la lista de aplicaciones.

## Fuera de alcance

- Diplomas de diplomados y fecha de inicio de clases
- Editor web del backend (`EditInBackendSystray`)
- Lógica de `is_diplomado()` / `irg_is_diplomado()`
