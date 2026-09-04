# Patron: hasattr no es seguro en QWeb de Odoo 16

Fecha: 2026-09-04

Modulo: `irg_campus_certificates_tile_qweb_fix`

## Decision reutilizable

En plantillas QWeb no usar `hasattr(...)`. En Odoo 16 `hasattr` no está en
`odoo.tools.safe_eval._BUILTINS`. QWeb evalúa `hasattr(...)` como `None(...)`
y lanza `TypeError: 'NoneType' object is not callable`.

Para un método de modelo, depender del módulo que lo define y llamarlo
directamente (`course_id.is_diplomado()`). El patrón defensivo
`not hasattr(record, 'metodo') or not record.metodo()` es válido en Python
normal y roto en QWeb.

## Motivos

- El tile `certificates_and_diplomas` usaba `hasattr` para no depender de
  `irg_diplomado_portal_request`. Al actualizar la vista en beta, `/campus/course/<id>`
  pasó a 500.
- Desinstalar el módulo que disparó el update no revierte la vista de la
  dependencia.

## Gotchas

- `ir.qweb._render` en tests de Odoo 16 devuelve `str`/`Markup`, no `bytes`.
- `op.course.create` en este runtime exige `lang`.
- Para tiles del campus, validar el arch combinado de
  `isep_website_custom.user_profile_content_details` y renderizar el `t-if`
  extraído; `/campus/course/<id>` en HttpCase depende de mucho contexto de perfil.
