# Forum Post Batch Visibility Controls

## Contexto

El modulo `irg_forum_batch_visibility` no solo limita foros (`forum.forum`), tambien ofrece visibilidad granular por publicacion (`forum.post`). Para publicaciones dentro de foros compartidos, la fuente de verdad es:

- `forum.post.visibility_batch_ids`: lotes que pueden visualizar la publicacion.
- `forum.post.excluded_visibility_batch_ids`: lotes que no pueden visualizar la publicacion.

## Regla Funcional

Un usuario puede leer una publicacion si:

- Puede ver el foro contenedor segun `_visibility_domain_for_user()`.
- Si la publicacion tiene lotes permitidos, el usuario pertenece a alguno de ellos.
- El usuario no pertenece a ningun lote excluido en la publicacion.

La exclusion gana siempre sobre la inclusion.

## Gotcha Tecnico

No basta con actualizar `ir.rule`. Algunos flujos usan `sudo()` o calculan destinatarios manualmente:

- `irg_forum_notice_popup` debe llamar a `_filter_visible_for_user()` porque el controlador busca publicaciones con `sudo()`.
- `irg_forum_email_notify` debe llamar a `_filter_partners_visible_for_post()` antes de crear `mail.mail`.
- **Filtro de Lotes Activos**: El modelo `op.batch` no tiene un campo `state`. Para filtrar lotes activos en dominios y búsquedas, se debe utilizar el campo booleano estándar `active` (`('active', '=', True)`).

## Validacion Usada

Se valido con:

- `py_compile` de los Python modificados.
- Parse XML de vistas y reglas.
- Actualizacion Odoo local en `test_irg_db` con `docker-compose.local.yml`.
- Assertions funcionales en Odoo shell con rollback para permitido, excluido, no permitido y herencia del foro.
